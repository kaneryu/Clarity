from __future__ import annotations

import logging
import time
from typing import Optional

from PySide6.QtCore import QObject, Signal, Slot, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from src import universal as universal
from src.providerInterface import Song
from src.misc.enumerations.Song import PlayingStatus

QTPLAYBACKSTATE_MAP = {
    QMediaPlayer.PlaybackState.PlayingState: PlayingStatus.PLAYING,
    QMediaPlayer.PlaybackState.PausedState: PlayingStatus.PAUSED,
    QMediaPlayer.PlaybackState.StoppedState: PlayingStatus.STOPPED,
    QMediaPlayer.MediaStatus.BufferingMedia: PlayingStatus.BUFFERING_LOCAL,
    QMediaPlayer.MediaStatus.LoadingMedia: PlayingStatus.BUFFERING_LOCAL,
    QMediaPlayer.MediaStatus.StalledMedia: PlayingStatus.BUFFERING_NETWORK,
    QMediaPlayer.MediaStatus.EndOfMedia: PlayingStatus.STOPPED,
}


class QtMediaPlayer(QObject):
    """Media playback engine using QtMultimedia implementing the MediaPlayer contract.

    Audio-only: No VideoOutput connected. Works best with FFmpeg backend (WebM/Opus).
    Falls back gracefully when MRL not yet available (NOT_READY state and async fetch).
    """

    NAME = "qt"

    playingStatusChanged = Signal(int)
    durationChanged = Signal()
    timeChanged = Signal(int)
    songChanged = Signal(int)
    prevSongOnSongChange = Signal(QObject)

    endReached = Signal()
    errorOccurred = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.logger = logging.getLogger("MediaPlayer.QtMultimedia")

        # State
        self._status: PlayingStatus = PlayingStatus.STOPPED
        self._current_song: Optional[Song] = None
        self._prev_song: Optional[Song] = None
        self._noMrl: bool = False
        self.__last_time_emit: float = 0.0

        # Qt multimedia objects
        self._audio = QAudioOutput(self)
        self._player = QMediaPlayer(self)
        self._player.setAudioOutput(
            self._audio
        )  # no video output attached => audio-only

        # Wire events
        self._player.playbackStateChanged.connect(self._onPlaybackState)
        self._player.mediaStatusChanged.connect(self._onMediaStatus)
        self._player.positionChanged.connect(self._onPositionChanged)
        self._player.durationChanged.connect(lambda _=None: self.durationChanged.emit())
        self._player.playbackStateChanged.connect(self.update_playing_status)
        # errorOccurred added in Qt6 API
        try:
            self._player.errorOccurred.connect(lambda err: self.errorOccurred.emit(err))  # type: ignore[attr-defined]
        except Exception:
            pass

    # -------- Protocol surface --------
    def isPlaying(self) -> bool:
        return self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState

    def get_playing_status(self) -> int:
        return QTPLAYBACKSTATE_MAP.get(
            self._player.playbackState(), PlayingStatus.ERROR
        ).value

    def update_playing_status(self) -> None:
        state = self._player.playbackState()
        mapped_status = QTPLAYBACKSTATE_MAP.get(state, PlayingStatus.ERROR)
        self.set_playing_status(mapped_status)

    def set_playing_status(self, value: PlayingStatus) -> None:
        if value != self._status:
            self._status = value
            self.playingStatusChanged.emit(int(value))

    def current_duration_s(self) -> int:
        d = self._player.duration()
        return int(d // 1000) if d and d > 0 else 0

    def current_time_s(self) -> int:
        p = self._player.position()
        return int(p // 1000) if p and p > 0 else 0

    def _set_source(self, mrl: str) -> None:
        # Ensure local file paths are converted to file:// URLs on Windows
        try:
            # Heuristic: treat as network URL if it has a scheme
            url = QUrl(mrl)
            if url.isValid() and url.scheme() in ("http", "https"):
                self._player.setSource(url)
                return
        except Exception:
            pass

        # Otherwise, assume local path; use fromLocalFile to generate file:/// URL
        self._player.setSource(QUrl.fromLocalFile(mrl))

    def play(self, song: Song) -> None:
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
        self._set_source(url)
        self._player.play()
        self.prevSongOnSongChange.emit(self._prev_song)
        self.songChanged.emit(-1)
        self.durationChanged.emit()

    def onSongMrlChanged(self, song: Song) -> None:
        if self._current_song is None or song is not self._current_song:
            return
        if getattr(song, "playbackReady", False) and self._noMrl:
            self.play(song)

    @Slot()
    def pause(self) -> None:
        self._player.pause()

    @Slot()
    def resume(self) -> None:
        self._player.play()

    @Slot()
    def stop(self) -> None:
        self._player.stop()
        self.set_playing_status(PlayingStatus.STOPPED)

    @Slot()
    def reload(self) -> None:
        if self._current_song is None:
            return
        url = self._current_song.get_best_playback_mrl()
        if not url:
            return
        pos = self._player.position()
        self._set_source(url)
        if pos > 0:
            self._player.setPosition(pos)
        self._player.play()

    def migrate(self, mrl: str) -> None:
        pos = self._player.position()
        self._set_source(mrl)
        if pos > 0:
            self._player.setPosition(pos)
        self._player.play()

    @Slot(int)
    def seek(self, seconds: int) -> None:
        if seconds < 0:
            raise ValueError("seconds must be >= 0")
        self._player.setPosition(seconds * 1000)

    @Slot(int)
    def aseek(self, seconds: int) -> None:
        self.seek(max(0, self.current_time_s() + seconds))

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
            self._player.deleteLater()
            self._audio.deleteLater()
            self.logger.info("QtMultimedia MediaPlayer destroyed")

    # -------- Optional future volume API --------
    def set_volume(self, volume01: float) -> None:
        v = max(0.0, min(1.0, float(volume01)))
        self._audio.setVolume(v)

    def get_volume(self) -> float:
        return float(self._audio.volume())

    # -------- Handlers --------
    def _onPlaybackState(self, state) -> None:
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.set_playing_status(PlayingStatus.PLAYING)
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.set_playing_status(PlayingStatus.PAUSED)
        else:
            # StoppedState
            self.set_playing_status(PlayingStatus.STOPPED)

    def _onMediaStatus(self, status) -> None:
        # Map key statuses to LOCAL vs NETWORK buffering and END
        if status in (
            QMediaPlayer.MediaStatus.BufferingMedia,
            QMediaPlayer.MediaStatus.LoadingMedia,
        ):
            # Local demux/decoder buffering; playback may continue
            self.set_playing_status(PlayingStatus.BUFFERING_LOCAL)
        elif status == QMediaPlayer.MediaStatus.StalledMedia:
            # A stall generally indicates network starvation; treat as NETWORK buffering
            self.set_playing_status(PlayingStatus.BUFFERING_NETWORK)
        elif status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.endReached.emit()
            self.set_playing_status(PlayingStatus.STOPPED)

    def _onPositionChanged(self, ms: int) -> None:
        now = time.time()
        if now - self.__last_time_emit < 0.5:
            return
        self.__last_time_emit = now
        self.timeChanged.emit(int(ms // 1000))
