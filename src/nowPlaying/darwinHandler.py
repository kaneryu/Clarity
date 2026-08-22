import inspect
import logging
import time

import MediaPlayer
from AppKit import NSImage
from AppKit import NSMakeRect
from AppKit import NSCompositingOperationSourceOver
from Foundation import NSMutableDictionary
from MediaPlayer import MPNowPlayingInfoCenter
from MediaPlayer import MPRemoteCommandCenter
from MediaPlayer import MPMediaItemArtwork
from MediaPlayer import MPMediaItemPropertyTitle
from MediaPlayer import MPMediaItemPropertyArtist
from MediaPlayer import MPMediaItemPropertyAlbumTitle
from MediaPlayer import MPMediaItemPropertyPlaybackDuration
from MediaPlayer import MPMediaItemPropertyArtwork
from MediaPlayer import MPMusicPlaybackState
from MediaPlayer import MPMusicPlaybackStatePlaying
from MediaPlayer import MPMusicPlaybackStatePaused
from MediaPlayer import MPNowPlayingInfoPropertyElapsedPlaybackTime
from MediaPlayer import MPNowPlayingInfoPropertyPlaybackRate
from MediaPlayer import MPNowPlayingInfoPropertyDefaultPlaybackRate
from MediaPlayer import MPNowPlayingInfoPropertyMediaType
from MediaPlayer import MPNowPlayingInfoMediaTypeAudio


from typing import runtime_checkable, Protocol, Any, Optional, Callable

from src.nowPlaying.HandlerEnum import HandlerType, Handlers
from src.nowPlaying.NowPlayingProtocol import NowPlaying

from enum import Enum

try:
    from MediaPlayer import (
        MPRemoteCommandHandlerStatusSuccess as _STATUS_SUCCESS,
        MPRemoteCommandHandlerStatusNoActionableNowPlayingItem as _STATUS_NO_HANDLER,
        MPRemoteCommandHandlerStatusCommandFailed as _STATUS_FAILED,
    )
except ImportError:  # older pyobjc bindings don't export these
    _STATUS_SUCCESS = 0
    _STATUS_NO_HANDLER = 110
    _STATUS_FAILED = 200

# (MPRemoteCommandCenter selector, Handlers attribute) for every command we claim.
# Two commands may share one handler; the trampolines are keyed by command name.
_COMMAND_MAP: tuple[tuple[str, str], ...] = (
    ("playCommand", "play"),
    ("pauseCommand", "pause"),
    ("stopCommand", "stop"),
    ("togglePlayPauseCommand", "togglePlayPause"),
    ("nextTrackCommand", "next"),
    ("previousTrackCommand", "previous"),
    ("seekForwardCommand", "fastForward"),
    ("seekBackwardCommand", "rewind"),
    ("skipForwardCommand", "fastForward"),
    ("skipBackwardCommand", "rewind"),
    ("changePlaybackPositionCommand", "seek"),
    ("likeCommand", "like"),
    ("dislikeCommand", "dislike"),
    ("bookmarkCommand", "bookmark"),
    ("changeShuffleModeCommand", "shuffleMode"),
    ("changeRepeatModeCommand", "repeatMode"),
)

# Reverse of _COMMAND_MAP: handler attribute -> every command it drives.
_HANDLER_COMMANDS: dict[str, tuple[str, ...]] = {}
for _commandName, _handlerName in _COMMAND_MAP:
    _HANDLER_COMMANDS[_handlerName] = _HANDLER_COMMANDS.get(_handlerName, ()) + (
        _commandName,
    )

# Commands whose event carries a payload the handler wants instead of the raw
# MPRemoteCommandEvent. Maps command name -> darwinHandler method that unpacks it.
_COMMAND_EVENT_ADAPTERS: dict[str, str] = {
    "changePlaybackPositionCommand": "_seekPositionFromEvent",
}

# macOS extrapolates the scrubber itself from (elapsed, rate, time-of-set), so
# re-pushing every player tick makes it stutter as it snaps back to a stale
# value. Only resync when the real position has drifted from what the OS would
# have predicted, or when this long has passed since the last push.
_TIMELINE_DRIFT_TOLERANCE = 1.5  # seconds
_TIMELINE_RESYNC_INTERVAL = 10.0  # seconds


class darwinHandler(NowPlaying):
    def __init__(self):
        self.logger = logging.getLogger("NowPlaying")

        self.nowPlayingCommandCenter = (
            MediaPlayer.MPRemoteCommandCenter.sharedCommandCenter()
        )
        self.nowPlayingInfoCenter = MediaPlayer.MPNowPlayingInfoCenter.defaultCenter()
        self.handlers = Handlers()

        # setNowPlayingInfo_ replaces the dictionary wholesale, so we keep our
        # own copy and merge into it -- otherwise a track change would wipe the
        # timeline keys and a timeline update would wipe the title.
        self._nowPlayingInfo: dict[Any, Any] = {}

        # Anchor for the scrubber extrapolation described above.
        self._timelineDuration = 0.0
        self._timelineAnchorPos = 0.0
        self._timelineAnchorAt = time.monotonic()
        self._timelineRate = 0.0

        # Seek bounds, refreshed by update_timeline. macOS has no API to
        # constrain the scrubber, so we clamp inside the seek handler instead.
        self._seekMin = 0.0
        self._seekMax: Optional[float] = None

        # Trampolines are registered once, up front, and resolve the handler at
        # invoke time. Registering `self.handlers.<name>` directly would hand
        # MediaPlayer whatever the attribute happened to be at construction time
        # -- None -- which the bridge turns into a nil block. MediaPlayer then
        # segfaults reading the block's invoke pointer the first time the user
        # touches a transport control.
        self._commandTargets: dict[str, Callable] = {}
        for commandName, handlerName in _COMMAND_MAP:
            command = getattr(self.nowPlayingCommandCenter, commandName, None)
            if command is None:
                self.logger.debug("MPRemoteCommandCenter has no %s", commandName)
                continue
            target = self._makeCommandTarget(commandName, handlerName)
            self._commandTargets[commandName] = target
            command().addTargetWithHandler_(target)
            # Commands are enabled by default, which makes the OS offer buttons
            # for things nothing has bound a handler to. Worse, an enabled
            # skipForward/skipBackward makes the Now Playing UI draw the +/-10s
            # buttons *instead of* next/previous track. Start everything off and
            # let set_handler switch on only what is actually wired up.
            command().setEnabled_(False)

    # ---------- remote command plumbing ----------

    def _makeCommandTarget(self, commandName: str, handlerName: str) -> Callable:
        """Build the block that MediaPlayer invokes for one remote command.

        The returned callable must never raise and must return an
        MPRemoteCommandHandlerStatus -- an exception escaping into Objective-C
        or a None return would take the process down with it.
        """
        adapterName = _COMMAND_EVENT_ADAPTERS.get(commandName)
        adapter = getattr(self, adapterName) if adapterName else None

        def target(event) -> int:
            handler = getattr(self.handlers, handlerName, None)
            if handler is None:
                self.logger.debug("No handler bound for %s", handlerName)
                return _STATUS_NO_HANDLER
            try:
                self._callHandler(handler, adapter(event) if adapter else event)
            except Exception:
                self.logger.exception("Now Playing handler %r failed", handlerName)
                return _STATUS_FAILED
            return _STATUS_SUCCESS

        return target

    def _callHandler(self, handler: Callable, event: Any) -> None:
        """Call a handler with (sender, event), or just (event) if it takes one arg.

        Matches the Windows convention, where handlers receive (sender, args).
        """
        try:
            argcount = len(inspect.signature(handler).parameters)
        except (TypeError, ValueError):
            argcount = 2  # not introspectable; assume the common convention
        if argcount >= 2:
            handler(self, event)
        else:
            handler(event)

    def _seekPositionFromEvent(self, event) -> float:
        """Unpack MPChangePlaybackPositionCommandEvent into clamped seconds."""
        position = float(event.positionTime())
        upper = self._seekMax if self._seekMax is not None else self._timelineDuration
        if upper > 0:
            position = min(position, upper)
        return max(self._seekMin, position)

    # ---------- now playing info ----------

    def _pushNowPlayingInfo(self, updates: dict[Any, Any]) -> None:
        """Merge keys into the now playing dictionary and hand it to the OS."""
        self._nowPlayingInfo.update(updates)
        self.nowPlayingInfoCenter.setNowPlayingInfo_(self._nowPlayingInfo)

    def _extrapolatedPosition(self, now: Optional[float] = None) -> float:
        """Where the OS currently believes the scrubber is."""
        now = time.monotonic() if now is None else now
        position = self._timelineAnchorPos + self._timelineRate * (
            now - self._timelineAnchorAt
        )
        if self._timelineDuration > 0:
            position = min(position, self._timelineDuration)
        return max(0.0, position)

    def _pushTimeline(
        self,
        duration: float,
        position: float,
        rate: float,
        now: Optional[float] = None,
    ) -> None:
        self._timelineDuration = duration
        self._timelineAnchorPos = position
        self._timelineRate = rate
        self._timelineAnchorAt = time.monotonic() if now is None else now
        self._pushNowPlayingInfo(
            {
                MPMediaItemPropertyPlaybackDuration: duration,
                MPNowPlayingInfoPropertyElapsedPlaybackTime: position,
                MPNowPlayingInfoPropertyPlaybackRate: rate,
                MPNowPlayingInfoPropertyDefaultPlaybackRate: 1.0,
            }
        )

    def _setPlaybackRate(self, rate: float) -> None:
        """Change rate, re-anchoring the scrubber at wherever it is right now."""
        self._pushTimeline(self._timelineDuration, self._extrapolatedPosition(), rate)

    def set_now_playing(
        self, title: str, artist: str, album: str, artwork: Optional[Any] = None
    ) -> None:
        """This function should set the currently playing song.

        Args:
            title (str): Title
            artist (str): Artist
            album (str): Album
            artwork (Optional[Any], optional): . Defaults to None.
        """
        self._nowPlayingInfo = {
            MPMediaItemPropertyTitle: title,
            MPMediaItemPropertyArtist: artist,
            # Tells the UI this is music, not a podcast/audiobook -- another
            # input to whether it draws next/previous or skip buttons.
            MPNowPlayingInfoPropertyMediaType: MPNowPlayingInfoMediaTypeAudio,
        }
        if album:
            self._nowPlayingInfo[MPMediaItemPropertyAlbumTitle] = album

        # temporary behavior. We're passed an URL to the image, so we'll download it.
        # In a future update, song images will be stored better so we won't have to download it in multiple places (like here)
        if artwork:
            try:
                from urllib.request import urlopen
                from io import BytesIO
                from PIL import Image

                with urlopen(artwork) as response:
                    image_data = response.read()
                    ns_image = NSImage.alloc().initWithData_(image_data)

                    def resize(size):
                        new = NSImage.alloc().initWithSize_(size)
                        new.lockFocus()
                        ns_image.drawInRect_fromRect_operation_fraction_(
                            NSMakeRect(0, 0, size.width, size.height),
                            NSMakeRect(
                                0, 0, ns_image.size().width, ns_image.size().height
                            ),
                            NSCompositingOperationSourceOver,
                            1.0,
                        )
                        new.unlockFocus()
                        return new

                    art = MPMediaItemArtwork.alloc().initWithBoundsSize_requestHandler_(
                        ns_image.size(), resize
                    )

                    self._nowPlayingInfo[MPMediaItemPropertyArtwork] = art
            except Exception as e:
                self.logger.error("Failed to load artwork: %s", e)

        # New track: the previous scrubber position is meaningless. This also
        # performs the setNowPlayingInfo_ call for the keys set above.
        self._pushTimeline(0.0, 0.0, self._timelineRate)

    def update_timeline(
        self,
        duration: float,
        position: float,
        *,
        min_seek=0.0,
        max_seek: Optional[float] = None,
    ) -> None:
        """Update the song's position on the timeline.

        Unlike the Windows backend this does NOT need calling every second --
        macOS advances the scrubber on its own. Redundant calls are filtered out
        here; only real discontinuities (a seek, a new duration) are pushed.

        Args:
            duration (float): Of the song, seconds
            position (float): Where you are, seconds
            min_seek (float, optional): Lower seek bound. Defaults to 0.0.
            max_seek (Optional[float], optional): Upper seek bound. Defaults to duration.
        """
        if duration is None or position is None:
            return
        duration = float(duration)
        position = float(position)

        # macOS can't constrain the scrubber's range, so remember the bounds and
        # apply them when a seek actually arrives.
        self._seekMin = max(0.0, float(min_seek or 0.0))
        self._seekMax = float(max_seek) if max_seek is not None else None

        now = time.monotonic()
        if (
            duration == self._timelineDuration
            and abs(position - self._extrapolatedPosition(now))
            <= _TIMELINE_DRIFT_TOLERANCE
            and now - self._timelineAnchorAt < _TIMELINE_RESYNC_INTERVAL
        ):
            return

        self._pushTimeline(duration, position, self._timelineRate, now=now)

    def playback_play(self) -> None:
        """This will be called whenever the song's state changes to playing. Update the OS accordingly."""
        self.nowPlayingInfoCenter.setPlaybackState_(
            MediaPlayer.MPMusicPlaybackStatePlaying
        )
        self._setPlaybackRate(1.0)

    def playback_pause(self) -> None:
        """This will be called whenever the song's state changes to paused. Update the OS accordingly."""
        self.nowPlayingInfoCenter.setPlaybackState_(
            MediaPlayer.MPMusicPlaybackStatePaused
        )
        self._setPlaybackRate(0.0)

    def playback_stop(self) -> None:
        """This will be called whenever the song's state changed to stopped. Update the OS accordingly."""
        self.nowPlayingInfoCenter.setPlaybackState_(
            MediaPlayer.MPMusicPlaybackStateStopped
        )
        self._setPlaybackRate(0.0)

    # ---------- command availability ----------

    def _setCommandEnabled(self, commandName: str, enabled: bool) -> None:
        command = getattr(self.nowPlayingCommandCenter, commandName, None)
        if command is None:
            self.logger.debug("MPRemoteCommandCenter has no %s", commandName)
            return
        command().setEnabled_(bool(enabled))

    def set_next_enabled(self, enabled: bool) -> None:
        self._setCommandEnabled("nextTrackCommand", enabled)

    def set_previous_enabled(self, enabled: bool) -> None:
        self._setCommandEnabled("previousTrackCommand", enabled)

    def set_handler(self, handler_type: HandlerType, handler: Callable) -> None:
        """Bind a handler. The trampoline registered in __init__ picks it up on the next command."""
        self.handlers.setHandler(handler_type, handler)
        # Now that something can service it, let the OS offer the command.
        for commandName in _HANDLER_COMMANDS.get(handler_type.value, ()):
            self._setCommandEnabled(commandName, True)
