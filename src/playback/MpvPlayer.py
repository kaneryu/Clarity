from __future__ import annotations

import logging
import time
from typing import Optional

from PySide6.QtCore import QObject, Signal, Slot, QTimer

from src import universal as universal
from src.innertube import Song
from src.misc.enumerations.Song import PlayingStatus

try:
    import mpv as _mpv
    import locale

    locale.setlocale(locale.LC_NUMERIC, "C")
except Exception as e:  # pragma: no cover - allow editor import without runtime dep
    raise ImportError("python-mpv is not installed or failed to import") from e


class MpvMediaPlayer(QObject):
    """Media playback engine using libmpv implementing the MediaPlayer contract.

    Notes:
    - Configured for audio-only (no video window) while fully supporting WebM/Opus, MP3, WAV, and HTTP(S) streaming.
    - All mpv callbacks are dispatched back to the Qt main thread via QTimer.singleShot.
    - Mirrors VLC backend behavior for MRL resolution and signal semantics.
    """

    NAME = "mpv"

    # Signal shapes must match Queue expectations
    playingStatusChanged = Signal(int)
    durationChanged = Signal()
    timeChanged = Signal(int)
    songChanged = Signal(int)
    prevSongOnSongChange = Signal(QObject)

    endReached = Signal()
    errorOccurred = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.logger = logging.getLogger("MediaPlayer.mpv")

        # Internal state
        self._status: PlayingStatus = PlayingStatus.STOPPED
        self._current_song: Optional[Song] = None
        self._prev_song: Optional[Song] = None
        self._noMrl: bool = False
        self.__last_time_emit: float = 0.0

        # mpv instance (audio only)
        locale.setlocale(locale.LC_NUMERIC, "C")
        self._mpv = _mpv.MPV(
            input_default_bindings=False,
            input_vo_keyboard=False,
            video=False,
            audio_display="no",
            ytdl=False,  # We already resolve URLs via Song
            # Slightly larger demuxer cache helps with network hiccups
            demuxer_max_back_bytes=50 * 1024 * 1024,
        )

        # Property observers
        self._mpv.observe_property("time-pos", self._on_time)
        self._mpv.observe_property("duration", self._on_duration)
        self._mpv.observe_property("pause", self._on_pause)
        self._mpv.observe_property("core-idle", self._on_idle)

        # Events (register using decorator API; dispatch back to Qt thread)
        @self._mpv.event_callback("end-file")
        def on_end_file(event):
            self._on_end_file(event)

        @self._mpv.event_callback("playback-restart")
        def on_playback_restart(event):  # noqa: ARG001
            self.set_playing_status(PlayingStatus.PLAYING)

        @self._mpv.event_callback("log-message")
        def on_log_message(level, prefix, text):  # noqa: ARG001
            self._emit_log(level, prefix, text)

        # Detect cache starvation: mpv sets pause when 'paused-for-cache' becomes True
        self._mpv.observe_property("paused-for-cache", self._on_paused_for_cache)
        # Detect seeks as local buffering
        self._mpv.observe_property("seeking", self._on_seeking)

    def _emit_end(self) -> None:
        self.endReached.emit()
        self.set_playing_status(PlayingStatus.STOPPED)

    def _emit_log(self, level, prefix, text) -> None:
        if level in ("error", "fatal"):
            self.errorOccurred.emit({"level": level, "prefix": prefix, "text": text})

    # ---------- Protocol surface ----------
    def isPlaying(self) -> bool:
        return bool(self._mpv) and not bool(self._mpv.pause)

    def get_playing_status(self) -> int:
        return int(self._status)

    def update_playing_status(self) -> None:
        if self._mpv is None:
            self.set_playing_status(PlayingStatus.STOPPED)
            return

        try:
            idle = bool(self._mpv.core_idle)
            paused = bool(self._mpv.pause)
            pfc = bool(getattr(self._mpv, "paused_for_cache", False))
        except Exception:
            idle, paused, pfc = True, False, False

        if idle:
            self.set_playing_status(PlayingStatus.STOPPED)
        elif pfc:
            self.set_playing_status(PlayingStatus.BUFFERING_NETWORK)
        elif paused:
            self.set_playing_status(PlayingStatus.PAUSED)
        else:
            self.set_playing_status(PlayingStatus.PLAYING)

    def set_playing_status(self, value: PlayingStatus) -> None:
        if value != self._status:
            self._status = value
            self.playingStatusChanged.emit(int(value))

    def current_duration_s(self) -> int:
        d = self._mpv.duration
        try:
            return int(d) if d and d > 0 else 0
        except Exception:
            return 0

    def current_time_s(self) -> int:
        t = self._mpv.time_pos
        try:
            return int(t) if t and t > 0 else 0
        except Exception:
            return 0

    def play(self, song: Song) -> None:
        # Reset if mpv is in an odd transient state (handled by immediate load anyway)
        self._prev_song = self._current_song
        self._current_song = song

        url = song.get_best_playback_mrl()
        if url is None:
            self.logger.info(
                f"No MRL found for song ({song.id} - {getattr(song, 'title', song.id)}), fetching now..."
            )
            self.set_playing_status(PlayingStatus.NOT_READY)
            self._noMrl = True
            self.songChanged.emit(-1)
            self.durationChanged.emit()
            universal.bgworker.addJob(func=song.get_playback)
            return

        self._noMrl = False
        self._mpv.play(url)
        self._mpv.pause = False
        # Initial load is considered local buffering until playback restarts
        self.set_playing_status(PlayingStatus.BUFFERING_LOCAL)
        self.songChanged.emit(-1)
        self.prevSongOnSongChange.emit(self._prev_song)
        self.durationChanged.emit()

    def onSongMrlChanged(self, song: Song) -> None:
        if self._current_song is None or song is not self._current_song:
            return
        if getattr(song, "playbackReady", False) and self._noMrl:
            # Resume play now that MRL exists
            self.play(song)
        else:
            # If already had an MRL, do nothing; Queue controls migrations separately
            pass

    @Slot()
    def pause(self) -> None:
        self._mpv.pause = True
        self.set_playing_status(PlayingStatus.PAUSED)

    @Slot()
    def resume(self) -> None:
        self._mpv.pause = False
        self.set_playing_status(PlayingStatus.PLAYING)

    @Slot()
    def stop(self) -> None:
        try:
            self._mpv.stop()
        finally:
            self.set_playing_status(PlayingStatus.STOPPED)

    @Slot()
    def reload(self) -> None:
        if self._current_song is None:
            return
        self.onSongMrlChanged(self._current_song)

    def migrate(self, mrl: str) -> None:
        pos = self.current_time_s()
        # Replace current file and try to preserve position
        try:
            self._mpv.command("loadfile", mrl, "replace", f"start={pos}")
            self.set_playing_status(PlayingStatus.BUFFERING)
        except Exception as e:  # pragma: no cover
            self.logger.exception("mpv migrate failed: %s", e)
            self.errorOccurred.emit(e)

    @Slot(int)
    def seek(self, seconds: int) -> None:
        if seconds < 0:
            raise ValueError("seconds must be >= 0")
        self._mpv.command("seek", seconds, "absolute")

    @Slot(int)
    def aseek(self, seconds: int) -> None:
        self._mpv.command("seek", seconds, "relative")

    @Slot(int)
    def pseek(self, percentage: int) -> None:
        if not (0 <= percentage <= 100):
            raise ValueError("percentage must be 0..100")
        dur = self.current_duration_s()
        if dur > 0:
            self.seek(int(dur * (percentage / 100.0)))

    def destroy(self) -> None:
        try:
            self.stop()
        finally:
            self._mpv.terminate()
            self.logger.info("mpv MediaPlayer destroyed")

    # ---------- Optional future volume API ----------
    def set_volume(self, volume01: float) -> None:
        """Set volume 0.0..1.0 (mapped to mpv 0..100)."""
        v = max(0.0, min(1.0, float(volume01)))
        self._mpv.volume = int(round(v * 100))

    def get_volume(self) -> float:
        v = self._mpv.volume or 0
        try:
            return max(0.0, min(1.0, float(v) / 100.0))
        except Exception:
            return 0.0

    # ---------- mpv callbacks (dispatch to Qt thread) ----------
    def _on_time(self, name, value):  # noqa: ARG002
        if value is None:
            return
        now = time.time()
        if now - self.__last_time_emit < 0.5:
            return
        self.__last_time_emit = now
        QTimer.singleShot(0, lambda v=int(value): self.timeChanged.emit(v))

    def _on_duration(self, name, value):  # noqa: ARG002
        QTimer.singleShot(0, self.durationChanged.emit)

    def _on_pause(self, name, paused):  # noqa: ARG002
        # If paused due to cache starvation, let the paused-for-cache observer handle status as BUFFERING_NETWORK
        if paused:
            try:
                pfc = getattr(self._mpv, "paused_for_cache", None)
                if pfc is None:
                    pfc = self._mpv.get_property("paused-for-cache")
            except Exception:
                pfc = False
            if pfc:
                return
        QTimer.singleShot(
            0,
            lambda: self.set_playing_status(
                PlayingStatus.PAUSED if paused else PlayingStatus.PLAYING
            ),
        )

    def _on_paused_for_cache(self, name, value):  # noqa: ARG002
        # When mpv pauses for cache, treat as NETWORK buffering
        if value:
            QTimer.singleShot(
                0, lambda: self.set_playing_status(PlayingStatus.BUFFERING_NETWORK)
            )

    def _on_seeking(self, name, value):  # noqa: ARG002
        if value:
            QTimer.singleShot(
                0, lambda: self.set_playing_status(PlayingStatus.BUFFERING_LOCAL)
            )

    def _on_idle(self, name, idle):  # noqa: ARG002
        if idle:
            QTimer.singleShot(0, lambda: self.set_playing_status(PlayingStatus.STOPPED))

    # Decide whether end-file truly means EOF; only emit end if near duration or reason is EOF
    def _on_end_file(self, event: _mpv.MpvEvent) -> None:
        def handle():
            eventdata = event.data
            try:
                reason = getattr(eventdata, "reason", None)
                """
                REASONS:
                ABORTED = 2
                EOF = 0
                ERROR = 4
                QUIT = 3
                REDIRECT = 5
                RESTARTED = 1
                error = 0
                """
                reason_name = (
                    "eof"
                    if reason == 0
                    else (
                        "error" if reason == 4 else "stop" if reason in (2, 3) else None
                    )
                )
            except Exception:
                reason_name = None

            # Handle explicit reasons first
            if reason_name == "eof":
                self._emit_end()
                return
            if reason_name in ("stop", "quit"):
                # User or programmatic stop
                # self.set_playing_status(PlayingStatus.STOPPED)
                # This is emitted way too often, let's just ignore it
                return
            if reason_name == "error":
                # Let UI know an error occurred; do not emit end
                self.errorOccurred.emit(
                    {"level": "error", "prefix": "mpv", "text": "end-file: error"}
                )
                self.set_playing_status(PlayingStatus.ERROR)
                return

            # Otherwise, verify time vs duration within tolerance
            try:
                cur = float(self._mpv.time_pos or 0)  # seconds
                dur = float(self._mpv.duration or 0)
            except Exception:
                cur, dur = 0.0, 0.0

            at_end = dur > 0 and cur >= (dur - 1.0)  # within 1s of end
            if at_end:
                self._emit_end()
            else:
                # Not actually at end; likely transient (e.g., cache/network hiccup). Ignore.
                self.logger.debug(
                    "mpv end-file ignored: not at end (cur=%s, dur=%s, reason=%s)",
                    cur,
                    dur,
                    reason_name,
                )

        handle()
