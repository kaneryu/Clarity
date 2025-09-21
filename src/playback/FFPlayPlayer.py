# filepath: src/innertube/player.py
from __future__ import annotations

import time
import logging
import platform
import ctypes


from typing import Optional, Protocol, Union, runtime_checkable, Any

from PySide6.QtCore import QObject, Signal, Slot, QTimer

from ffpyplayer.player import MediaPlayer as FFMediaPlayer 

from src import universal as universal
from src.innertube.song import Song
from src.misc.enumerations.Song import PlayingStatus


class FFPlayMediaPlayer(QObject):
    """Media playback engine using FFplay implementing the MediaPlayer contract.

    Responsibilities:
    - Manage FFplay instance, media player, and events
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

    # New: cross-thread event bridge for ffpyplayer callback
    _ffThreadEvent = Signal(str, object)

    def __init__(self) -> None:
        super().__init__()
        self.logger = logging.getLogger("MediaPlayer.FFPlayPlayer")

        self._player: Optional[FFMediaPlayer] = None
        self._playingStatus: PlayingStatus = PlayingStatus.STOPPED
        self._current_song: Optional[Song] = None
        self._noMrl: bool = False

        self._timeTimer: QTimer = QTimer(self)
        self._timeTimer.setInterval(500)
        self._timeTimer.timeout.connect(self._on_time_tick)

        self._last_pts_s: int = 0
        self._last_duration_s: int = 0

        # Connect cross-thread callback signal to main-thread handler
        self._ffThreadEvent.connect(self._handle_ff_event)
    
    def destroy(self) -> None:
        """Clean up resources, stop playback, disconnect signals, prepare for deletion."""
        self.stop()
        self._ffThreadEvent.disconnect(self._handle_ff_event)
        self._timeTimer.timeout.disconnect(self._on_time_tick)
        self.deleteLater()

    # -------------------- Internal helpers --------------------
    def _emit_status(self, status: PlayingStatus) -> None:
        if self._playingStatus != status:
            self._playingStatus = status
            self.playingStatusChanged.emit(int(status))

    def _ff_callback(self, selector: str, value) -> None:
        # Called by ffpyplayer internal threads: emit a Qt signal to hop to the main thread.
        self._ffThreadEvent.emit(selector, value)
        # self._handle_ff_event(selector, value)

    @Slot(str, object)
    def _handle_ff_event(self, selector: str, value) -> None:
        if selector == "eof":
            self.logger.info("FFPlay EOF reached")
            self._emit_status(PlayingStatus.STOPPED)
            self.endReached.emit()
        elif selector.endswith(":error"):
            self.logger.error("FFPlay error from %s: %s", selector, value)
            self.errorOccurred.emit({"selector": selector, "error": value})
        elif selector.endswith(":exit"):
            self.logger.debug("FFPlay thread exit: %s", selector)
        elif selector == "display_sub":
            # Not used for audio playback in this app; ignore.
            pass

    def _dispose_player(self) -> None:
        if self._player is not None:
            try:
                self._player.close_player()
            except Exception as e:
                self.logger.exception("Error closing FFPlay player: %s", e)
            self._player = None
        self._timeTimer.stop()
        self._last_pts_s = 0
        self._last_duration_s = 0

    def _ensure_player(self, url: str) -> None:
        # Create new ffpyplayer instance
        try:
            self._player = FFMediaPlayer(
                url,
                callback=self._ff_callback,
                ff_opts={
                    # Keep defaults sensible; we don't display frames
                    "autoexit": True,   # eof stops internally
                    "sync": "audio",    # use audio clock
                    "paused": False,    # start playing immediately
                    "vn": True,       # no video
                },
                thread_lib = "python"
            )
            # Initial decode/demux buffering is local
            self._emit_status(PlayingStatus.BUFFERING_LOCAL)
            if not self._timeTimer.isActive():
                self._timeTimer.start()
        except Exception as e:
            self.logger.exception("Failed to create FFPlay player: %s", e)
            self.errorOccurred.emit(e)
            self._emit_status(PlayingStatus.STOPPED)

    def _on_time_tick(self) -> None:
        # Poll current time and duration; emit changes.
        if self._player is None:
            return
        try:
            pts = self._player.get_pts() or 0.0
            pts_s = int(pts)
            if pts_s != self._last_pts_s:
                self._last_pts_s = pts_s
                # Consider transition to PLAYING when time advances
                if self._playingStatus not in (PlayingStatus.PLAYING, PlayingStatus.PAUSED):
                    self._emit_status(PlayingStatus.PLAYING)
                self.timeChanged.emit(pts_s)

            md = self._player.get_metadata() or {}
            dur = md.get("duration") or 0
            dur_s = int(dur)
            if dur_s != self._last_duration_s:
                self._last_duration_s = dur_s
                self.durationChanged.emit()
        except Exception as e:
            # Don't spam; emit once and stop timer until recovery/reload.
            self.logger.exception("FFPlay polling error: %s", e)
            self._timeTimer.stop()
            self.errorOccurred.emit(e)

    # -------------------- Public properties --------------------
    def isPlaying(self) -> bool:
        return self._playingStatus == PlayingStatus.PLAYING

    def get_playing_status(self) -> int:
        if self._player is None:
            return int(PlayingStatus.NOT_READY)
        return int(self._playingStatus)

    def set_playing_status(self, value: PlayingStatus) -> None:
        if value not in PlayingStatus:
            raise ValueError("Invalid PlayingStatus value")
        self._emit_status(value)

    def current_duration_s(self) -> int:
        if self._player is None:
            return 0
        try:
            md = self._player.get_metadata() or {}
            dur = md.get("duration") or 0
            return int(dur)
        except Exception:
            return 0

    def current_time_s(self) -> int:
        if self._player is None:
            return 0
        try:
            return int(self._player.get_pts() or 0.0)
        except Exception:
            return 0

    # -------------------- Control API --------------------
    def play(self, song: Song) -> None:
        self._current_song = song

        url = song.get_best_playback_MRL()
        if url is None:
            self.logger.info("No MRL for song (%s - %s), fetching...", song.id, song.title)
            self._noMrl = True
            self._emit_status(PlayingStatus.NOT_READY)
            self.songChanged.emit()
            self.durationChanged.emit()
            universal.bgworker.add_job(func=song.get_playback)
            return

        # Have URL; ensure player
        self._noMrl = False
        # Reset previous player
        self._dispose_player()
        # Create and start new player
        self._ensure_player(url)
        self.songChanged.emit()
        # Duration will be emitted when metadata becomes available

    def onSongMrlChanged(self, song: Song) -> None:
        if self._current_song is None:
            return
        if song == self._current_song:
            self.logger.info("Current Song MRL Changed")
            if getattr(song, "playbackReady", False) and self._noMrl:
                self.play(song)
            else:
                if getattr(song, "playbackReady", False):
                    self.logger.debug("Current Song is playback ready; MRL was already set.")
                else:
                    self.logger.debug("Current Song is not playback ready; skipping MRL set.")

    # Alias to match Queue.songMrlChanged call site
    def on_song_mrl_changed(self, song: Song) -> None:
        self.onSongMrlChanged(song)

    @Slot()
    def pause(self) -> None:
        if self._player is None:
            return
        try:
            self._player.set_pause(True)
            self._emit_status(PlayingStatus.PAUSED)
        except Exception as e:
            self.logger.exception("FFPlay pause error: %s", e)
            self.errorOccurred.emit(e)

    @Slot()
    def resume(self) -> None:
        if self._player is None:
            return
        try:
            self._player.set_pause(False)
            self._emit_status(PlayingStatus.PLAYING)
        except Exception as e:
            self.logger.exception("FFPlay resume error: %s", e)
            self.errorOccurred.emit(e)

    @Slot()
    def stop(self) -> None:
        # Do not emit endReached here; just stop.
        self._dispose_player()
        self._emit_status(PlayingStatus.STOPPED)

    @Slot()
    def reload(self) -> None:
        if self._current_song is not None:
            self.play(self._current_song)

    def migrate(self, mrl: str) -> None:
        paused = False
        t = 0.0
        try:
            if self._player is not None:
                paused = bool(self._player.get_pause())
                t = float(self._player.get_pts() or 0.0)
        except Exception:
            pass

        self._dispose_player()
        self._ensure_player(mrl)

        # Try to restore position/state shortly after player starts
        def restore():
            try:
                if self._player is None:
                    return
                if t > 0:
                    self._player.seek(t, relative=False, accurate=False)
                if paused:
                    self._player.set_pause(True)
                    self._emit_status(PlayingStatus.PAUSED)
            except Exception as e:
                self.logger.exception("FFPlay migrate restore error: %s", e)
        QTimer.singleShot(50, restore)

    def _seek(self, target_s: float, relative: bool = False) -> None:
        if self._player is None:
            raise ValueError("No Media Loaded")
        if not relative:
            # Validate bounds if duration known
            dur = self.current_duration_s()
            if dur and (target_s < 0 or target_s > dur):
                raise ValueError("Time must be between 0 and media length")
        try:
            self._player.seek(target_s, relative=relative, accurate=False)
            # Mirror VLC behavior: report PLAYING after seek
            QTimer.singleShot(0, lambda: self._emit_status(PlayingStatus.PLAYING))
        except Exception as e:
            self.logger.exception("FFPlay seek error: %s", e)
            raise

    @Slot(int)
    def seek(self, seconds: int) -> None:
        self._seek(float(seconds), relative=False)

    @Slot(int)
    def aseek(self, seconds: int) -> None:
        self._seek(float(seconds), relative=True)

    @Slot(int)
    def pseek(self, percentage: int) -> None:
        if percentage < 0 or percentage > 100:
            raise ValueError("Percentage must be between 0 and 100")
        dur = self.current_duration_s()
        if not dur:
            raise ValueError("Unknown media duration")
        self._seek(dur * (percentage / 100.0), relative=False)