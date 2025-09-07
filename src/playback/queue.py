import time
import logging
import enum

from typing import Union

from PySide6.QtCore import Property as QProperty, Signal, Slot, Qt, QObject, QSize, QModelIndex, QPersistentModelIndex, QAbstractListModel, QMutex, QMutexLocker

from src import universal as g
from src import cacheManager
import src.discotube.presence as presence
import src.wintube.winSMTC as winSMTC

# Import Song and PlayingStatus without creating circular imports.
# song.py must not import Queue; it should use g.queueInstance when needed.
from src.innertube.song import Song, PlayingStatus
from src.playback.player import MediaPlayer


class LoopType(enum.Enum):
    """Loop Types"""
    NONE = 0  # Halt after playing all songs
    SINGLE = 1  # Repeat the current song
    ALL = 2  # Repeat all songs in the queue


class QueueModel(QAbstractListModel):
    def __init__(self):
        super().__init__()
        self._queueIds = []
        self._queue: list[Song] = []

    def rowCount(self, parent=QModelIndex()):
        return len(self._queue)

    def count(self):
        return len(self._queue)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            return self._queue[index.row()].title
        if role == Qt.ItemDataRole.EditRole:
            return self._queue[index.row()]
        if role == Qt.ItemDataRole.UserRole + 1:
            return self._queue[index.row()].artist
        if role == Qt.ItemDataRole.UserRole + 2:
            return self._queue[index.row()].duration
        if role == Qt.ItemDataRole.UserRole + 3:
            return "placeholder"
        if role == Qt.ItemDataRole.UserRole + 4:
            return self._queue[index.row()].id
        if role == Qt.ItemDataRole.UserRole + 5:
            return index.row()
        return None

    def roleNames(self):
        return {
            Qt.ItemDataRole.DisplayRole: b"title",
            Qt.ItemDataRole.UserRole + 1: b"artist",
            Qt.ItemDataRole.UserRole + 2: b"length",
            Qt.ItemDataRole.UserRole + 3: b"thumbnail",
            Qt.ItemDataRole.UserRole + 4: b"id",
            Qt.ItemDataRole.UserRole + 5: b"index",
            Qt.ItemDataRole.EditRole: b"qobject",
        }

    def headerData(self, section, orientation, role=...):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return "Song"
            else:
                return f"Song {section}"
        return None

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if role == Qt.ItemDataRole.EditRole and index.isValid():
            self._queue[index.row()] = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def setQueue(self, queue):
        self.beginResetModel()
        self._queue = queue
        self.endResetModel()

    def removeItem(self, index):
        if 0 <= index < len(self._queue):
            self.beginRemoveRows(QModelIndex(), index, index)
            del self._queue[index]
            self.endRemoveRows()

    def moveItem(self, from_index, to_index):
        if 0 <= from_index < len(self._queue) and 0 <= to_index < len(self._queue):
            self.beginMoveRows(QModelIndex(), from_index, from_index, QModelIndex(), to_index)
            self._queue.insert(to_index, self._queue.pop(from_index))
            self.endMoveRows()

    def insertRows(self, row: int, count: int = 1, parent: QModelIndex | QPersistentModelIndex = QModelIndex()):
        self.beginInsertRows(QModelIndex(), row, row + count - 1)
        self._queue.insert(row, [[] for _ in range(count)])  # type: ignore[arg-type]
        self.endInsertRows()


class Queue(QObject):
    """Queue managing the list, Discord presence, and WinSMTC; playback is delegated to MediaPlayer."""

    queueChanged = Signal()
    songChanged = Signal()
    pointerMoved = Signal()
    playingStatusChanged = Signal(int)
    durationChanged = Signal()
    timeChanged = Signal(int)

    nextSongSignal = Signal()
    prevSongSignal = Signal()

    singleton: Union["Queue", None] = None

    def __new__(cls, *args, **kwargs) -> "Queue":
        if cls.singleton is None:
            cls.singleton = super(Queue, cls).__new__(cls, *args, **kwargs)
        return cls.singleton

    def __init__(self):
        if hasattr(self, 'initialized'):
            return

        super().__init__()
        self.initialized = True
        self.logger = logging.getLogger("Queue")
        self._pointer = 0

        self._mutex = QMutex()
        self._queueAccessMutex = QMutex()

        self.loop: LoopType = LoopType.NONE
        self.queueModel = QueueModel()

        self.cache = cacheManager.getCache("queue_cache")

        # Media player engine
        self._player = MediaPlayer()
        self._player.songChanged.connect(self.songChanged)
        self._player.durationChanged.connect(self.durationChanged)
        self._player.timeChanged.connect(self._on_time_changed)
        self._player.playingStatusChanged.connect(self._on_playing_status_changed)
        self._player.endReached.connect(self._on_end_reached)
        self._player.errorOccurred.connect(self._on_vlc_error)

        # WinSMTC integration
        self.winPlayer = winSMTC._get_player()
        self.songChanged.connect(self.updateWinPlayer)
        winSMTC.Handlers.setHandler(winSMTC.HandlerType.PLAY, lambda x, y: self.resume())
        winSMTC.Handlers.setHandler(winSMTC.HandlerType.PAUSE, lambda x, y: self.pause())
        winSMTC.Handlers.setHandler(winSMTC.HandlerType.STOP, lambda x, y: self.stop())
        winSMTC.Handlers.setHandler(winSMTC.HandlerType.NEXT, lambda x, y: self.nextSongSignal.emit())
        winSMTC.Handlers.setHandler(winSMTC.HandlerType.PREVIOUS, lambda x, y: self.prevSongSignal.emit())

        # Presence and state
        self.purgetries = {}
        self.presence = presence.initialize_discord_presence(self)

        # Relay control signals
        self.playingStatusChanged.connect(lambda: self.currentSongObject.checkPlaybackReady())  # type: ignore[attr-defined]
        self.nextSongSignal.connect(lambda: self.next())
        self.prevSongSignal.connect(lambda: self.prev())
        
        self.currentSongObject: Song

    # ---------- Internal handlers delegating from MediaPlayer ----------
    def _on_time_changed(self, seconds: int):
        # Update SMTC timeline and bubble the signal
        winSMTC.update_timeline(
            duration_s=self.currentSongDuration,  # type: ignore[arg-type]
            position_s=self.currentSongTime  # type: ignore[arg-type]
        )
        self.timeChanged.emit(seconds)

    def _on_playing_status_changed(self, status: int):
        # Re-emit for QML bindings
        self.playingStatusChanged.emit(status)
        # Sync SMTC basic state
        if status == PlayingStatus.PLAYING:
            winSMTC.playback_play()
        elif status == PlayingStatus.PAUSED:
            winSMTC.playback_pause()

    def _on_end_reached(self):
        winSMTC.playback_stop()
        self.next()

    def _on_vlc_error(self, event):
        self.logger.error("VLC Error")
        self.logger.error("VLC error event: %s", event)
        g.bgworker.add_job(self.refetch)

    # ---------- Public API ----------
    @Slot(Song)
    def songMrlChanged(self, song: Song):
        self._player.on_song_mrl_changed(song)

    def updateWinPlayer(self):
        winSMTC.set_now_playing(
            title=self.currentSongTitle,  # type: ignore
            artist=self.currentSongChannel,  # type: ignore
            album_title="",
            art_uri=self.currentSongObject.largestThumbnailUrl  # type: ignore
        )
        if self.queue and self.pointer < len(self.queue) - 1:
            winSMTC.set_next_enabled(True)
        else:
            winSMTC.set_next_enabled(False)

        if self.queue and self.pointer > 0:
            winSMTC.set_previous_enabled(True)
        else:
            winSMTC.set_previous_enabled(False)

    @QProperty(bool, notify=playingStatusChanged)
    def isPlaying(self):
        with QMutexLocker(self._mutex):
            return self._player.get_playing_status() == PlayingStatus.PLAYING

    @QProperty(int, notify=playingStatusChanged)
    def playingStatus(self):
        with QMutexLocker(self._mutex):
            return self._player.get_playing_status()

    @playingStatus.setter
    def playingStatus(self, value: PlayingStatus):
        self._player.set_playing_status(value)

    @QProperty(list, notify=queueChanged)
    def queue(self):
        with QMutexLocker(self._queueAccessMutex):
            return self.queueModel._queue

    @queue.setter
    def queue(self, value):
        with QMutexLocker(self._queueAccessMutex):
            self.queueChanged.emit()
            self.setQueue(value, skipSetData=True)

    @QProperty(list, notify=queueChanged)
    def queueIds(self) -> list:
        with QMutexLocker(self._queueAccessMutex):
            return self.queueModel._queueIds

    @QProperty(str, notify=songChanged)
    def currentSongTitle(self):
        with QMutexLocker(self._mutex):
            return self.info(self.pointer)["title"]

    @QProperty(str, notify=songChanged)
    def currentSongChannel(self):
        with QMutexLocker(self._mutex):
            return self.info(self.pointer)["uploader"]

    @QProperty(str, notify=songChanged)
    def currentSongDescription(self):
        with QMutexLocker(self._mutex):
            return self.info(self.pointer)["description"]

    @QProperty(str, notify=songChanged)
    def currentSongId(self):
        return self.queueIds[self.pointer]  # type: ignore[index]

    @QProperty(QObject, notify=songChanged)
    def currentSongObject(self):
        return self.queue[self.pointer]

    @QProperty(int, notify=pointerMoved)
    def pointer(self):
        return self._pointer

    @pointer.setter
    def pointer(self, value):
        if value == -1:
            self._pointer = len(self.queue) - 1  # special case for setting pointer to last song
        if value < 0 or value >= len(self.queue):
            raise ValueError("Pointer must be between 0 and length of queue")
        self.pointerMoved.emit()
        self._pointer = value

    @QProperty(int, notify=songChanged)
    def currentSongDuration(self):
        return self._player.current_duration_s()

    @QProperty(int, notify=songChanged)
    def currentSongTime(self):
        return self._player.current_time_s()

    @QProperty(int, notify=songChanged)
    def songFinishesAt(self):
        return time.time() + self.currentSongDuration - self.currentSongTime  # type: ignore[operator]

    def checkError(self, url: str):
        r = g.networkManager.get(url)
        return r is None or getattr(r, "status_code", None) != 200

    @Slot(result=dict)
    def getCurrentInfo(self) -> dict:
        return self.info(self.pointer)

    @Slot(list, bool)
    def setQueue(self, queue: list, skipSetData: bool = False):
        for i in queue:
            self.add(i)

    def refetch(self):
        self.purgetries[self.queueIds[self.pointer]] = self.purgetries.get(self.queueIds[self.pointer], 0) + 1  # type: ignore[index]
        if self.purgetries[self.queueIds[self.pointer]] > 1:  # type: ignore[index]
            self.logger.error("Purge Failed")
            self.stop()
            return
        else:
            self.queue[self.pointer].purge_playback()
        self.play()

    @Slot(str)
    def goToSong(self, id: str):
        if not id in self.queue:
            self.add(id)
        self.pointer = self.queueIds.index(id)  # type: ignore[attr-defined]
        self.play()

    @Slot()
    def pause(self):
        self._player.pause()

    @Slot()
    def resume(self):
        self._player.resume()

    @Slot()
    def play(self):
        self._player.play(self.queue[self.pointer])

    def migrate(self, MRL):
        self._player.migrate(MRL)

    @Slot()
    def stop(self):
        self._player.stop()
        winSMTC.playback_stop()

    @Slot()
    def reload(self):
        self._player.reload()

    @Slot(int)
    def setPointer(self, index: int):
        self.pointer = index
        self.play()

    @Slot()
    def next(self):
        self.logger.info("Next")
        self.logger.info("Pointer: %s, Length: %s", self.pointer, len(self.queue))
        if self.pointer == len(self.queue) - 1:
            self.logger.info("Queue Finished")
            if self.loop == LoopType.SINGLE:
                self.play()  # pointer doesn't change, song doesn't change
                return
            elif self.loop == LoopType.ALL:
                self.pointer = 0
                self.play()
                return
            else:
                self.logger.info("Queue Exhausted")
                self.stop()
                return
        self.pointer += 1
        self.play()

    @Slot()
    def prev(self):
        self.pointer = self.pointer - 1 if self.pointer > 0 else 0
        self.play()

    def info(self, pointer: int):
        if len(self.queue) == 0:
            return {
                "title": "No Songs",
                "uploader": "No Songs",
                "description": "No Songs"
            }

        song_ = self.queue[pointer]
        return {
            "title": song_.title,
            "uploader": song_.artist,
            "description": song_.description
        }

    def add(self, id: str, index: int = -1, goto: bool = False):
        s: Song = Song(id=id)
        if s.source == None:  # if we need to get the songinfo
            coro = s.get_info(g.asyncBgworker.API)
            future = g.asyncBgworker.run_coroutine_threadsafe(coro) if hasattr(g.asyncBgworker, 'run_coroutine_threadsafe') else None
            if future is None:
                # Fallback to accessing the loop directly as in original code
                import asyncio
                future = asyncio.run_coroutine_threadsafe(coro, g.asyncBgworker.event_loop)
            future.result()

        if index == -1:
            self.queueModel.insertRows(len(self.queue), 1)
            self.queueModel.setData(self.queueModel.index(len(self.queue) - 1), s, Qt.ItemDataRole.EditRole)
            self.queueIds.append(s.id)  # type: ignore
        else:
            self.queueModel.insertRows(index, 1)
            self.queueModel.setData(self.queueModel.index(index), s, Qt.ItemDataRole.EditRole)
            self.queueIds.insert(index, s.id)  # type: ignore

        if goto:
            self.pointer = len(self.queue) - 1 if index == -1 else index
            self.play()

        s.playbackReadyChanged.connect(lambda: self.songMrlChanged(s))

    @Slot(int)
    def seek(self, time: int):
        self._player.seek(time)

    @Slot(int)
    def aseek(self, time: int):
        self._player.aseek(time)

    @Slot(int)
    def pseek(self, percentage: int):
        self._player.pseek(percentage)
