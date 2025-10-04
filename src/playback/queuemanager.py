import time
import logging
import traceback

from typing import Union, Any, cast

from PySide6.QtCore import Property as QProperty, Signal, Slot, Qt, QObject, QSize, QModelIndex, QPersistentModelIndex, QAbstractListModel, QMutex, QMutexLocker, QTimer, QThread

from src import universal as universal
from src import cacheManager
from src.misc.enumerations.Queue import LoopType
from src.misc.settings import Settings, getSetting
import src.discotube.presence as presence
import src.wintube.winSMTC as winSMTC

# Import Song and PlayingStatus without creating circular imports.
# song.py must not import Queue; it should use g.queueInstance when needed.
from src.innertube.song import Song, PlayingStatus
from src.innertube.album import Album
from playback.MediaPlayerProtocol import MediaPlayer
from src.playback.VlcPlayer import VLCMediaPlayer
from src.playback.FFPlayPlayer import FFPlayMediaPlayer
from src.playback.MpvPlayer import MpvMediaPlayer
from src.playback.QtMediaPlayer import QtMediaPlayer


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
        # Insert actual Song placeholders at the position
        for i in range(count):
            self._queue.insert(row + i, None)  # type: ignore[arg-type]
        self.endInsertRows()


class Queue(QObject):
    """Queue managing the list, Discord presence, and WinSMTC; playback is delegated to MediaPlayer."""

    queueChanged = Signal()
    songChanged = Signal(int) # emits PREVIOUS song index
    pointerMoved = Signal()
    playingStatusChanged = Signal(int)
    durationChanged = Signal()
    timeChanged = Signal(int)

    nextSongSignal = Signal()
    prevSongSignal = Signal()
    gotoSignal = Signal(int)

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
        self.queue: list[Song]
        self.queueIds: list[str]
        self.queueModel = QueueModel()

        # Media player engine: start with VLC to satisfy type expectations, then swap if needed
        self._player = cast(MediaPlayer, VLCMediaPlayer())
        self.setupPlayer(self._player)
        self.updateMediaPlayer()  # Initialize based on current setting
        self.logger.info(f"Media player backend set to: {getSetting('mediaPlayerBackend').value}")
        print(f"Media player backend set to: {getSetting('mediaPlayerBackend').value}")
        getSetting("mediaPlayerBackend").valueChanged.connect(lambda: self.updateMediaPlayer(True))

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
        self.playingStatusChanged.connect(lambda: self.currentSongObject.playingStatusChanged.emit(self.playingStatus))  # type: ignore[attr-defined]
        self.songChanged.connect(self.songChangedPlaybackStatusUpdate)
        self.nextSongSignal.connect(lambda: self.next())
        self.prevSongSignal.connect(lambda: self.prev())
        self.gotoSignal.connect(lambda index: self.goto(index))
        

        # Debounce state for Next presses
        self._next_press_count = 0
        self._next_press_exhausted = False
        self._next_timer = QTimer(self)
        self._next_timer.setSingleShot(True)
        self._next_timer.timeout.connect(self._finalize_next_sequence)

        # Debounce state for Prev presses
        self._prev_press_count = 0
        self._prev_timer = QTimer(self)
        self._prev_timer.setSingleShot(True)
        self._prev_timer.timeout.connect(self._finalize_prev_sequence)
    
    @Slot(int)
    def songChangedPlaybackStatusUpdate(self, prevpointer):
        if not prevpointer == -1:
            song: Song = self.queue[prevpointer]
            song.playingStatusChanged.emit(PlayingStatus.NOT_PLAYING)
    
    def updateMediaPlayer(self, fallback: bool = True):
        backend = getSetting("mediaPlayerBackend").value
        setting = getSetting("mediaPlayerBackend")
        
        if backend == "vlc" and not isinstance(self._player, VLCMediaPlayer):
            try:
                self.swapPlayers(VLCMediaPlayer())
                setting.value = "vlc"
                
            except Exception as e:
                self.logger.exception("Failed to initialize vlc backend: %s", e)
                if fallback and self._player is None:
                    self.swapPlayers(MpvMediaPlayer())        
        elif backend == "ffplay" and not isinstance(self._player, FFPlayMediaPlayer):
            try:
                self.swapPlayers(FFPlayMediaPlayer())
                setting.value = "ffplay"
                
            except Exception as e:
                self.logger.exception("Failed to initialize ffplay backend: %s", e)
                if fallback and self._player is None:
                    self.swapPlayers(MpvMediaPlayer()) 
        elif backend == "mpv":
            try:
                if not isinstance(self._player, MpvMediaPlayer):
                    self.swapPlayers(MpvMediaPlayer())
                setting.value = "mpv"
                
            except Exception as e:
                self.logger.exception("Failed to initialize mpv backend: %s", e)
                traceback.print_exc()
                if fallback and self._player is None:
                    self.swapPlayers(VLCMediaPlayer())
        elif backend == "qt":
            try:
                if not isinstance(self._player, QtMediaPlayer):
                    self.swapPlayers(QtMediaPlayer())
                setting.value = "qt"
                
            except Exception as e:
                self.logger.exception("Failed to initialize QtMultimedia backend: %s", e)
                if fallback and self._player is None:
                    self.swapPlayers(MpvMediaPlayer())        
        elif fallback and self._player is None:
            self.swapPlayers(MpvMediaPlayer())  # Default to MPV if no valid backend is set
            

        if backend is not self._player.NAME: setting.setValue(self._player.NAME)

    def setupPlayer(self, player: MediaPlayer):
        # Optional runtime enforcement since Protocol is runtime_checkable
        if not isinstance(player, MediaPlayer):
            raise TypeError("player must satisfy the MediaPlayer protocol")
        self._player = player
        self._player.songChanged.connect(self.songChanged)
        self._player.durationChanged.connect(self.durationChanged)
        self._player.timeChanged.connect(self._on_time_changed)
        self._player.playingStatusChanged.connect(self._on_playing_status_changed)
        self._player.endReached.connect(self._on_end_reached)
        self._player.errorOccurred.connect(self._on_error)
    
    def swapPlayers(self, new_player: MediaPlayer):
        if not isinstance(new_player, MediaPlayer):
            raise TypeError("new_player must satisfy the MediaPlayer protocol")
        
        old_player = self._player

        # Disconnect old player's signals
        old_player.songChanged.disconnect(self.songChanged)
        old_player.durationChanged.disconnect(self.durationChanged)
        old_player.timeChanged.disconnect(self._on_time_changed)
        old_player.playingStatusChanged.disconnect(self._on_playing_status_changed)
        old_player.endReached.disconnect(self._on_end_reached)
        old_player.errorOccurred.disconnect(self._on_error)

        # Switch to new player and wire it
        self._player = new_player
        self.setupPlayer(self._player)

        # Destroy old after swap
        old_player.destroy()
        
        if self.isPlaying or self.playingStatus == PlayingStatus.BUFFERING or self.playingStatus == PlayingStatus.BUFFERING_NETWORK:
            self.play()  # Restart playback with new player
            self.resume()
        else:
            self.play()
            self.pause()  # Prepare but stay paused if not playing
        self.logger.warning(f"Swapped to new media player backend: {type(new_player).__name__}", {"notify": True})
    
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

    def _on_error(self, event):
        self.logger.error("Player Error")
        self.logger.error("Player error event: %s", event)
        universal.bgworker.add_job(self.refetch)

    # Finalize debounced Next presses: perform single play/stop
    def _finalize_next_sequence(self):
        presses = self._next_press_count
        self._next_press_count = 0
        if self._next_press_exhausted:
            self._next_press_exhausted = False
            self.stop()
            return
        if not self.queue:
            return
        self.play()

    # Finalize debounced Prev presses: perform single play
    def _finalize_prev_sequence(self):
        self._prev_press_count = 0
        if not self.queue:
            return
        self.play()

    # ---------- Public API ----------
    @Slot(Song)
    def songMrlChanged(self, song: Song):
        self._player.onSongMrlChanged(song)

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
            return self._player.get_playing_status() == int(PlayingStatus.PLAYING)

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
        r = universal.networkManager.get(url)
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
        if not len(self.queue) == 0:
            self._player.play(self.queue[self.pointer])
        else:
            self.logger.warning("Play called with empty queue")

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
        self.goto(index)

    @Slot()
    def next(self):
        self.logger.info("Next (debounced)")
        if not self.queue:
            return

        # Grow debounce window with each press; cap to 500ms
        self._next_press_count = min(self._next_press_count + 1, 500)

        # Apply one logical next step without starting playback
        if self.pointer == len(self.queue) - 1:
            self.logger.info("Pointer at end")
            if self.loop == LoopType.SINGLE:
                # Repeat current track (no pointer change); update bindings
                self.songChanged.emit(self.pointer)
            elif self.loop == LoopType.ALL:
                prevpointer = self.pointer
                self.pointer = 0
                self.songChanged.emit(prevpointer)
            else:
                # Exhausted and no looping: stop on finalize
                self._next_press_exhausted = True
        else:
            prevpointer = self.pointer
            self.pointer += 1
            self.songChanged.emit(prevpointer)

        # Start/reset timer: 100ms per press, up to 500ms
        interval_ms = min(100 * self._next_press_count, 500)
        self._next_timer.start(interval_ms)

    @Slot()
    def prev(self):
        self.logger.info("Prev (debounced)")
        if not self.queue:
            return

        # Grow debounce window with each press; cap to 500ms
        self._prev_press_count = min(self._prev_press_count + 1, 500)

        # Apply one logical prev step without starting playback
        if self.pointer == 0:
            if self.loop == LoopType.SINGLE:
                # Repeat current track
                self.songChanged.emit(self.pointer)
            elif self.loop == LoopType.ALL:
                prevpointer = self.pointer
                self.pointer = len(self.queue) - 1
                self.songChanged.emit(prevpointer)
            else:
                # No looping: stay at start
                self.songChanged.emit(self.pointer)
        else:
            prevpointer = self.pointer
            self.pointer -= 1
            self.songChanged.emit(prevpointer)

        # Start/reset timer: 100ms per press, up to 500ms
        interval_ms = min(100 * self._prev_press_count, 500)
        self._prev_timer.start(interval_ms)
    
    @Slot(int)
    def goto(self, index: int):
        if index < 0 or index >= len(self.queue):
            raise ValueError("Index out of bounds")
        prevpointer = self.pointer
        self.pointer = index
        self.songChanged.emit(prevpointer)
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
        
        # Insert song into model immediately (even if metadata isn't loaded yet)
        insert_index = len(self.queue) if index == -1 else index
        self.queueModel.insertRows(insert_index, 1)
        self.queueModel.setData(self.queueModel.index(insert_index), s, Qt.ItemDataRole.EditRole)
        self.queueIds.insert(insert_index, s.id)

        # If metadata needs to be fetched, do it asynchronously
        if s.source is None:
            def on_info_fetched():
                # When metadata arrives, notify the model that this row changed
                try:
                    row_index = self.queueIds.index(s.id)
                    model_index = self.queueModel.index(row_index)
                    self.queueModel.dataChanged.emit(model_index, model_index)
                    self.logger.debug(f"Song metadata loaded: {s.title}")
                except ValueError:
                    # Song was removed from queue before metadata loaded
                    pass
            
            # Connect to signal before starting async fetch
            s.songInfoFetched.connect(on_info_fetched)
            
            # Submit async task without blocking
            coro = s.get_info(universal.asyncBgworker.API)
            if hasattr(universal.asyncBgworker, 'run_coroutine_threadsafe'):
                universal.asyncBgworker.run_coroutine_threadsafe(coro)
            else:
                import asyncio
                asyncio.run_coroutine_threadsafe(coro, universal.asyncBgworker.event_loop)

        if goto:
            self.pointer = insert_index
            self.play()

        s.playbackReadyChanged.connect(lambda: self.songMrlChanged(s))
    
    def gotoOrAdd(self, id: str):
        if id in self.queueIds: # type: ignore[operator]
            self.pointer = self.queueIds.index(id)  # type: ignore[attr-defined]
            self.play()
        else:
            self.add(id, goto=False)
            self.pointer = len(self.queue) - 1
            # Use QTimer to defer play() to next event loop iteration
            # This allows Song.__init__ file I/O to complete before playback attempt
            from PySide6.QtCore import QTimer
            QTimer.singleShot(0, self.play)

    @Slot(int)
    def seek(self, time: int):
        self._player.seek(time)

    @Slot(int)
    def aseek(self, time: int):
        self._player.aseek(time)

    @Slot(int)
    def pseek(self, percentage: int):
        self._player.pseek(percentage)


def addAlbumToQueue(album: Album, goto: bool = False):
    if not album.songs or len(album.songs) == 0:
        logging.getLogger("Queue").warning("Album has no songs, cannot add to queue")
        return
    q = universal.queueInstance
    start_index = len(q.queue)
    for song in album.songs:
        q.add(song.id)
    if goto and len(album.songs) > 0:
        q.pointer = start_index
        q.play()