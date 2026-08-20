import asyncio
import winrt.windows.media.control as wmctrl
import winrt.windows.media.playback as wmp
import winrt.windows.media as wmedia
import winrt.windows.storage.streams as wss
import winrt.windows.foundation as wf
from datetime import datetime, timezone, timedelta

import enum
import typing

from src.nowPlaying.HandlerEnum import HandlerType, Handlers
from src.nowPlaying.NowPlayingProtocol import NowPlaying


class WinSMTC(NowPlaying):

    def __init__(self):
        self._player: wmp.MediaPlayer = self._get_player()
        self.handlers = Handlers()
        self.button_token = None

        self.set_button_handler(self.buttonhandler)

    def update_timeline(
        self,
        duration_s: float | None = None,
        position_s: float | None = None,
        *,
        min_seek_s: float = 0.0,
        max_seek_s: float | None = None,
    ) -> None:
        """Report timeline to SMTC so the OS shows duration/position. Call whenever things change."""
        smtc = self._player.system_media_transport_controls
        tl = wmedia.SystemMediaTransportControlsTimelineProperties()
        # Start and min seek
        tl.start_time = timedelta(seconds=0)
        tl.min_seek_time = timedelta(seconds=max(0.0, float(min_seek_s)))
        # End/max seek
        end = (
            timedelta(seconds=float(duration_s))
            if duration_s is not None
            else timedelta(seconds=0)
        )
        tl.end_time = end
        tl.max_seek_time = (
            timedelta(seconds=float(max_seek_s)) if max_seek_s is not None else end
        )
        # Position
        if position_s is not None:
            tl.position = timedelta(seconds=max(0.0, float(position_s)))
        # Stamp update time in UTC
        # tl.last_updated_time = datetime.now(timezone.utc)
        smtc.update_timeline_properties(tl)

    def playback_play(self) -> None:
        self._get_player().system_media_transport_controls.playback_status = (
            wmedia.MediaPlaybackStatus.PLAYING
        )

    def playback_pause(self) -> None:
        self._get_player().system_media_transport_controls.playback_status = (
            wmedia.MediaPlaybackStatus.PAUSED
        )

    def playback_stop(self) -> None:
        self._get_player().system_media_transport_controls.playback_status = (
            wmedia.MediaPlaybackStatus.STOPPED
        )

    def set_now_playing(
        self,
        title: str = "",
        artist: str = "",
        album_title: str = "",
        art_uri: str | None = None,
    ) -> None:
        """Publish metadata for your own app's SMTC session. art_uri can be an http(s) or file URI."""
        p = self._get_player()

        smtc = p.system_media_transport_controls
        du = smtc.display_updater
        du.type = wmedia.MediaPlaybackType.MUSIC
        music = du.music_properties
        music.title = title or ""
        music.artist = artist or ""
        music.album_title = album_title or ""
        if art_uri:
            du.thumbnail = wss.RandomAccessStreamReference.create_from_uri(
                wf.Uri(art_uri)
            )
        du.update()
        smtc.playback_status = wmedia.MediaPlaybackStatus.PLAYING

    def _get_player(self):
        if self._player is None:
            self._player = wmp.MediaPlayer()
            smtc = self._player.system_media_transport_controls
            smtc.is_enabled = True
            smtc.is_play_enabled = True
            smtc.is_pause_enabled = True
            smtc.is_stop_enabled = True
        return self._player

    def set_album_art_file(self, path: str) -> None:
        """Set album art from a local file path."""
        from pathlib import Path

        p = self._get_player()
        du = p.system_media_transport_controls.display_updater
        file_uri = wf.Uri(Path(path).resolve().as_uri())
        du.thumbnail = wss.RandomAccessStreamReference.create_from_uri(file_uri)
        du.update()

    def clear_now_playing(self) -> None:
        p = self._get_player()
        du = p.system_media_transport_controls.display_updater
        du.clear_all()
        du.update()

    def buttonhandler(
        self, sender, args: wmedia.SystemMediaTransportControlsButtonPressedEventArgs
    ) -> None:
        """Default handler for SMTC button presses."""
        match args.button:
            case wmedia.SystemMediaTransportControlsButton.PLAY:
                if self.handlers.play:
                    self.handlers.play(sender, args)
            case wmedia.SystemMediaTransportControlsButton.PAUSE:
                if self.handlers.pause:
                    self.handlers.pause(sender, args)
            case wmedia.SystemMediaTransportControlsButton.STOP:
                if self.handlers.stop:
                    self.handlers.stop(sender, args)
            case wmedia.SystemMediaTransportControlsButton.NEXT:
                if self.handlers.next:
                    self.handlers.next(sender, args)
            case wmedia.SystemMediaTransportControlsButton.PREVIOUS:
                if self.handlers.previous:
                    self.handlers.previous(sender, args)
            case wmedia.SystemMediaTransportControlsButton.FAST_FORWARD:
                if self.handlers.fast_forward:
                    self.handlers.fast_forward(sender, args)
            case wmedia.SystemMediaTransportControlsButton.REWIND:
                if self.handlers.rewind:
                    self.handlers.rewind(sender, args)

    def set_button_handler(self, handler) -> None:
        """Register a callback(sender, args) for SMTC button presses. Replaces any existing handler."""
        smtc = self._get_player().system_media_transport_controls
        if self.button_token is not None:
            try:
                smtc.remove_button_pressed(self.button_token)
            except Exception:
                pass
            self.button_token = None
        self.button_token = smtc.add_button_pressed(handler)

    def set_handler(
        self, handler_type: "HandlerType", handler: typing.Callable
    ) -> None:
        """Set a handler for a specific SMTC button press."""
        self.handlers.setHandler(handler_type, handler)

    def set_next_enabled(self, enabled: bool) -> None:
        smtc = self._get_player().system_media_transport_controls
        smtc.is_next_enabled = enabled

    def set_previous_enabled(self, enabled: bool) -> None:
        smtc = self._get_player().system_media_transport_controls
        smtc.is_previous_enabled = enabled


def set_transport_capabilities(
    *,
    play=True,
    pause=True,
    stop=True,
    next=True,
    previous=True,
    seek=True,
    fast_forward=False,
    rewind=False,
) -> None:
    smtc = _get_player().system_media_transport_controls
    smtc.is_enabled = True
    smtc.is_play_enabled = bool(play)
    smtc.is_pause_enabled = bool(pause)
    smtc.is_stop_enabled = bool(stop)
    smtc.is_next_enabled = bool(next)
    smtc.is_previous_enabled = bool(previous)
    smtc.is_seek_enabled = bool(seek)
    smtc.is_fast_forward_enabled = bool(fast_forward)
    smtc.is_fast_rewind_enabled = bool(rewind)
