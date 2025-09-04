import time
import logging
import platform
import ctypes
import enum

from typing import Union

from PySide6.QtCore import Property as QProperty, Signal, Slot, Qt, QObject, QSize, QModelIndex, QPersistentModelIndex, QAbstractListModel, QMutex, QMutexLocker, QMetaObject, QTimer

import vlc  # type: ignore[import-untyped]

from src import universal as g
from src import cacheManager
import src.discotube.presence as presence
import src.wintube.winSMTC as winSMTC

# Import Song and PlayingStatus without creating circular imports.
# song.py must not import Queue; it should use g.queueInstance when needed.
from src.innertube.song import Song, PlayingStatus


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
    """Combined Queue and Player"""

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

        vlc_args = ["h254-fps=15", "network-caching", "file-caching", "verbose=1", "vv", "log-verbose=3"]
        self.instance: vlc.Instance = vlc.Instance(vlc_args)

        def strToCtypes(s: str) -> ctypes.c_char_p:
            return ctypes.c_char_p(s.encode('utf-8'))

        vlc.libvlc_set_user_agent(self.instance, strToCtypes(f"Clarity {str(g.version)}"), strToCtypes(f"Clarity/{str(g.version)} Python/{platform.python_version()}"))

        self.player: vlc.MediaPlayer = self.instance.media_player_new()
        self.eventManager: vlc.EventManager = self.player.event_manager()

        self._mutex = QMutex()
        self._queueAccessMutex = QMutex()

        self.loop: LoopType = LoopType.NONE
        self.queueModel = QueueModel()

        self.cache = cacheManager.getCache("queue_cache")

        self.eventManager.event_attach(vlc.EventType.MediaPlayerEndReached, self.songFinished)
        self.eventManager.event_attach(vlc.EventType.MediaPlayerEncounteredError, self.on_vlc_error)
        self.eventManager.event_attach(vlc.EventType.MediaPlayerPaused, self.onPauseEvent)
        self.eventManager.event_attach(vlc.EventType.MediaPlayerPlaying, self.onPlayEvent)
        self.eventManager.event_attach(vlc.EventType.MediaPlayerBuffering, self.onBufferingEvent)
        self.eventManager.event_attach(vlc.EventType.MediaPlayerTimeChanged, self.onTimeChangedEvent)

        # Just found out vlc.State exists, implement it later

        self.winPlayer = winSMTC._get_player()
        self.songChanged.connect(self.updateWinPlayer)

        winSMTC.Handlers.setHandler(winSMTC.HandlerType.PLAY, lambda x, y: self.resume())
        winSMTC.Handlers.setHandler(winSMTC.HandlerType.PAUSE, lambda x, y: self.pause())
        winSMTC.Handlers.setHandler(winSMTC.HandlerType.STOP, lambda x, y: self.stop())
        winSMTC.Handlers.setHandler(winSMTC.HandlerType.NEXT, lambda x, y: self.nextSongSignal.emit())
        winSMTC.Handlers.setHandler(winSMTC.HandlerType.PREVIOUS, lambda x, y: self.prevSongSignal.emit())

        self.__bufflastTime: float = 0
        self.__playlastTime: float = 0
        self._playingStatus = PlayingStatus.STOPPED

        self.queue: list[Song]
        self.pointer: int
        self.currentSongObject: Song

        self.noMrl = False

        self.purgetries = {}
        self.presence = presence.initialize_discord_presence(self)

        self.queueIds: list[str]

        self.playingStatusChanged.connect(lambda: self.currentSongObject.checkPlaybackReady())  # type: ignore[attr-defined]
        self.nextSongSignal.connect(lambda: self.next())
        self.prevSongSignal.connect(lambda: self.prev())

    @Slot(Song)
    def songMrlChanged(self, song: Song):
        if song == self.currentSongObject:
            self.logger.info("Current Song MRL Changed")
            if song.playbackReady and self.noMrl:  # if the song is now pb ready, we can set the MRL
                self.play()
            else:
                if song.playbackReady:
                    self.logger.debug("Current Song is playback ready, and the MRL was already set, so we don't need to do anything.")
                else:
                    self.logger.debug("Current Song is not playback ready, so we don't set the MRL.")

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

    def onPlayEvent(self, event):
        self.logger.debug("Play Event")
        self._playingStatus = PlayingStatus.PLAYING
        self.playingStatusChanged.emit(self._playingStatus)
        winSMTC.playback_play()

    def onPauseEvent(self, event):
        self.logger.debug("Pause Event")
        self._playingStatus = PlayingStatus.PAUSED
        self.playingStatusChanged.emit(self._playingStatus)
        winSMTC.playback_pause()

    def onBufferingEvent(self, event):
        if time.time() - self.__bufflastTime < 1:
            return
        self.__bufflastTime = time.time()
        self._playingStatus = PlayingStatus.BUFFERING
        self.playingStatusChanged.emit(self._playingStatus)
        self.logger.debug("Buffering Event")

    def onTimeChangedEvent(self, event):
        if time.time() - self.__playlastTime < 0.5:
            return
        self.__playlastTime = time.time()
        if not self.playingStatus == PlayingStatus.PLAYING:
            self._playingStatus = PlayingStatus.PLAYING
            self.playingStatusChanged.emit(self._playingStatus)
            self.logger.debug("Time Changed Event")

        winSMTC.update_timeline(
            duration_s=self.currentSongDuration,  # type: ignore[arg-type]
            position_s=self.currentSongTime  # type: ignore[arg-type]
        )
        self.timeChanged.emit(self.currentSongTime)  # type: ignore[union-attr]

    @QProperty(bool, notify=playingStatusChanged)
    def isPlaying(self):
        with QMutexLocker(self._mutex):
            return self._playingStatus == PlayingStatus.PLAYING

    @QProperty(int, notify=playingStatusChanged)
    def playingStatus(self):
        with QMutexLocker(self._mutex):
            if self.player.get_media() is None:
                return PlayingStatus.NOT_READY
            return self._playingStatus

    @playingStatus.setter
    def playingStatus(self, value: PlayingStatus):
        if value not in PlayingStatus:
            raise ValueError("Invalid PlayingStatus value")
        self._playingStatus = value
        self.playingStatusChanged.emit(self._playingStatus)

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
        try:
            return self.player.get_length() // 1000
        except OSError:
            return 0

    @QProperty(int, notify=songChanged)
    def currentSongTime(self):
        try:
            if self.player.get_media() is None:
                return 0
            return self.player.get_time() // 1000
        except OSError:
            return 0

    @QProperty(int, notify=songChanged)
    def songFinishesAt(self):
        return time.time() + self.currentSongDuration - self.currentSongTime  # type: ignore[operator]

    def checkError(self, url: str):
        r = g.networkManager.get(url)
        return r.status_code != 200

    @Slot(result=dict)
    def getCurrentInfo(self) -> dict:
        return self.info(self.pointer)

    @Slot(list, bool)
    def setQueue(self, queue: list, skipSetData: bool = False):
        for i in queue:
            self.add(i)

    def songFinished(self, event):
        self.logger.info("Song Finished")
        self.logger.info("Player state: %s", self.player.get_state())
        winSMTC.playback_stop()

        # Queue the method call to happen on the object's thread
        QMetaObject.invokeMethod(self, "next", Qt.ConnectionType.QueuedConnection)

    def on_vlc_error(self, event):
        self.logger.error("VLC Error")
        self.logger.error("VLC error event: %s", event)
        g.bgworker.add_job(self.refetch)

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
        self.player.pause()

    @Slot()
    def resume(self):
        self.player.play()

    @Slot()
    def play(self):
        if self.player.get_state() in [vlc.State.Error, vlc.State.Opening, vlc.State.Buffering]:
            self.logger.warning(f"Player in unstable state {self.player.get_state()}, delaying operation")
            QTimer.singleShot(100, self.play)  # Retry a bit later
            return

        # If stopping previous media, add a small delay
        if self.player.get_media() is not None:
            self.player.stop()  # Stop the current media
            self.player.set_media(None)  # Reset the media to avoid issues when adding a song that doesn't have a MRL
            # Add a brief delay to allow VLC to clean up
            QTimer.singleShot(10, self._do_play)
        else:
            self._do_play()

    def _do_play(self):
        def Media(mrl):
            media: vlc.Media = self.instance.media_new(mrl)
            media.add_option("http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Herring/97.1.8280.8")
            media.add_option("http-referrer=https://www.youtube.com/")
            return media

        url = self.queue[self.pointer].get_best_playback_MRL()
        if url is None:
            self.logger.info(f"No MRL found for song ({self.queue[self.pointer].id} - {self.queue[self.pointer].title}), fetching now...")
            self.playingStatus = PlayingStatus.NOT_READY  # type: ignore[assignment]
            self.noMrl = True
            self.songChanged.emit()
            self.durationChanged.emit()
            g.bgworker.add_job(func=self.queue[self.pointer].get_playback)
            return

        self.noMrl = False

        self.player.set_media(Media(url))
        self.player.play()
        self.songChanged.emit()
        self.durationChanged.emit()

    def migrate(self, MRL):
        paused = (self.player.is_playing() == 0)
        newMedia = self.instance.media_new(MRL)
        self.player.pause()
        t = self.player.get_time()
        self.player.set_media(newMedia)
        if not paused:
            self.player.play()
        else:
            self.player.pause()
        self.player.set_time(t)

    @Slot()
    def stop(self):
        self.player.stop()
        winSMTC.playback_stop()

    @Slot()
    def reload(self):
        self.play()

    @Slot(int)
    def setPointer(self, index: int):
        self.pointer = index
        self.reload()

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

    def _seek(self, seek_time: int):
        if seek_time < 0 or seek_time > self.player.get_length():
            raise ValueError("Time must be between 0 and video length")
        if self.player.get_media() is not None:
            self.player.set_time(seek_time)
            time.sleep(0.1)
            self.onPlayEvent(None)
        else:
            raise ValueError("No Media Loaded")

    @Slot(int)
    def seek(self, time: int):
        self._seek(time * 1000)

    @Slot(int)
    def aseek(self, time: int):
        self._seek(self.player.get_time() + time * 1000)

    @Slot(int)
    def pseek(self, percentage: int):
        if percentage < 0 or percentage > 100:
            raise ValueError("Percentage must be between 0 and 100")
        self._seek(self.player.get_length() * percentage // 100)
