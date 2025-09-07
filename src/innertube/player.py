# filepath: src/innertube/player.py
from __future__ import annotations

import time
import logging
import platform
import ctypes

from typing import Optional

from PySide6.QtCore import QObject, Signal, Slot, Qt, QTimer

import vlc  # type: ignore[import-untyped]

from src import universal as g
from src.innertube.song import Song, PlayingStatus


class MediaPlayer(QObject):
    """Media playback engine using VLC.

    Responsibilities:
    - Manage VLC instance, media player, and events
    - Control playback (play/pause/resume/stop/seek)
    - Emit playback-related signals
    - Handle MRL fetching and retry flow
    """

    # Reuse signal shapes used by Queue so Queue can re-emit them unchanged
    playingStatusChanged = Signal(int)
    durationChanged = Signal()
    timeChanged = Signal(int)
    songChanged = Signal()

    # Lifecycle/control signals for the queue to react
    endReached = Signal()
    errorOccurred = Signal(object)  # payload: error/event object

    def __init__(self) -> None:
        super().__init__()
        self.logger = logging.getLogger("MediaPlayer")

        # VLC init
        vlc_args = [
            "h254-fps=15",
            "network-caching",
            "file-caching",
            "verbose=1",
            "vv",
            "log-verbose=3",
        ]
        self.instance: vlc.Instance = vlc.Instance(vlc_args)

        def strToCtypes(s: str) -> ctypes.c_char_p:
            return ctypes.c_char_p(s.encode("utf-8"))

        vlc.libvlc_set_user_agent(
            self.instance,
            strToCtypes(f"Clarity {str(g.version)}"),
            strToCtypes(f"Clarity/{str(g.version)} Python/{platform.python_version()}"),
        )

        self.player: vlc.MediaPlayer = self.instance.media_player_new()
        self.eventManager: vlc.EventManager = self.player.event_manager()

        # Internal state
        self._playingStatus: PlayingStatus = PlayingStatus.STOPPED
        self._current_song: Optional[Song] = None
        self._noMrl: bool = False

        # Throttle timers for events
        self.__bufflastTime: float = 0
        self.__playlastTime: float = 0

        # Event wiring
        self.eventManager.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_song_finished)
        self.eventManager.event_attach(vlc.EventType.MediaPlayerEncounteredError, self._on_vlc_error)
        self.eventManager.event_attach(vlc.EventType.MediaPlayerPaused, self._on_pause_event)
        self.eventManager.event_attach(vlc.EventType.MediaPlayerPlaying, self._on_play_event)
        self.eventManager.event_attach(vlc.EventType.MediaPlayerBuffering, self._on_buffering_event)
        self.eventManager.event_attach(vlc.EventType.MediaPlayerTimeChanged, self._on_time_changed_event)

    # -------------------- Public properties --------------------
    def isPlaying(self) -> bool:
        return self._playingStatus == PlayingStatus.PLAYING

    def get_playing_status(self) -> int:
        # If media not yet set, advertise NOT_READY
        if self.player.get_media() is None:
            return int(PlayingStatus.NOT_READY)
        return int(self._playingStatus)

    def set_playing_status(self, value: PlayingStatus) -> None:
        if value not in PlayingStatus:
            raise ValueError("Invalid PlayingStatus value")
        self._playingStatus = value
        self.playingStatusChanged.emit(int(self._playingStatus))

    def current_duration_s(self) -> int:
        try:
            return int(self.player.get_length() // 1000)
        except OSError:
            return 0

    def current_time_s(self) -> int:
        try:
            if self.player.get_media() is None:
                return 0
            return int(self.player.get_time() // 1000)
        except OSError:
            return 0

    # -------------------- Control API --------------------
    def play(self, song: Song):
        # If player is in a transient or error state, retry shortly
        if self.player.get_state() in [vlc.State.Error, vlc.State.Opening, vlc.State.Buffering]:
            self.logger.warning(f"Player in unstable state {self.player.get_state()}, delaying operation")
            QTimer.singleShot(100, lambda: self.play(song))
            return

        self._current_song = song

        # Stop/reset previous media to avoid VLC issues
        if self.player.get_media() is not None:
            self.player.stop()
            self.player.set_media(None)
            QTimer.singleShot(10, lambda: self._do_play(song))
        else:
            self._do_play(song)

    def _do_play(self, song: Song):
        def Media(mrl: str) -> vlc.Media:
            media: vlc.Media = self.instance.media_new(mrl)
            media.add_option(
                "http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Herring/97.1.8280.8"
            )
            media.add_option("http-referrer=https://www.youtube.com/")
            return media

        url = song.get_best_playback_MRL()
        if url is None:
            self.logger.info(
                f"No MRL found for song ({song.id} - {song.title}), fetching now..."
            )
            self.set_playing_status(PlayingStatus.NOT_READY)
            self._noMrl = True
            self.songChanged.emit()
            self.durationChanged.emit()
            g.bgworker.add_job(func=song.get_playback)
            return

        self._noMrl = False
        self.player.set_media(Media(url))
        self.player.play()
        self.songChanged.emit()
        self.durationChanged.emit()

    def on_song_mrl_changed(self, song: Song):
        if self._current_song is None:
            return
        if song == self._current_song:
            self.logger.info("Current Song MRL Changed")
            if getattr(song, "playbackReady", False) and self._noMrl:
                # If previously missing MRL and now ready, resume play
                self.play(song)
            else:
                if getattr(song, "playbackReady", False):
                    self.logger.debug("Current Song is playback ready, and the MRL was already set.")
                else:
                    self.logger.debug("Current Song is not playback ready, so we don't set the MRL.")

    @Slot()
    def pause(self):
        self.player.pause()

    @Slot()
    def resume(self):
        self.player.play()

    @Slot()
    def stop(self):
        self.player.stop()
        # Let Queue decide what to do with WinSMTC, we only emit status via events

    @Slot()
    def reload(self):
        if self._current_song is not None:
            self.play(self._current_song)

    def migrate(self, mrl: str):
        paused = (self.player.is_playing() == 0)
        newMedia = self.instance.media_new(mrl)
        self.player.pause()
        t = self.player.get_time()
        self.player.set_media(newMedia)
        if not paused:
            self.player.play()
        else:
            self.player.pause()
        self.player.set_time(t)

    def _seek(self, seek_time_ms: int):
        if seek_time_ms < 0 or seek_time_ms > self.player.get_length():
            raise ValueError("Time must be between 0 and video length")
        if self.player.get_media() is not None:
            self.player.set_time(seek_time_ms)
            time.sleep(0.1)
            self._on_play_event(None)
        else:
            raise ValueError("No Media Loaded")

    @Slot(int)
    def seek(self, seconds: int):
        self._seek(seconds * 1000)

    @Slot(int)
    def aseek(self, seconds: int):
        self._seek(self.player.get_time() + seconds * 1000)

    @Slot(int)
    def pseek(self, percentage: int):
        if percentage < 0 or percentage > 100:
            raise ValueError("Percentage must be between 0 and 100")
        self._seek(self.player.get_length() * percentage // 100)

    # -------------------- VLC event handlers --------------------
    def _on_play_event(self, event):
        self.logger.debug("Play Event")
        self._playingStatus = PlayingStatus.PLAYING
        self.playingStatusChanged.emit(int(self._playingStatus))

    def _on_pause_event(self, event):
        self.logger.debug("Pause Event")
        self._playingStatus = PlayingStatus.PAUSED
        self.playingStatusChanged.emit(int(self._playingStatus))

    def _on_buffering_event(self, event):
        if time.time() - self.__bufflastTime < 1:
            return
        self.__bufflastTime = time.time()
        self._playingStatus = PlayingStatus.BUFFERING
        self.playingStatusChanged.emit(int(self._playingStatus))
        self.logger.debug("Buffering Event")

    def _on_time_changed_event(self, event):
        if time.time() - self.__playlastTime < 0.5:
            return
        self.__playlastTime = time.time()
        if self._playingStatus != PlayingStatus.PLAYING:
            self._playingStatus = PlayingStatus.PLAYING
            self.playingStatusChanged.emit(int(self._playingStatus))
            self.logger.debug("Time Changed Event")
        # Emit timeline in seconds
        self.timeChanged.emit(self.current_time_s())

    def _on_song_finished(self, event):
        self.logger.info("Song Finished")
        self.logger.info("Player state: %s", self.player.get_state())
        self.endReached.emit()

    def _on_vlc_error(self, event):
        self.logger.error("VLC Error")
        self.logger.error("VLC error event: %s", event)
        self.errorOccurred.emit(event)
