import enum
import logging
import asyncio
import json
import time
from typing import List, Dict, Optional, Any

from PySide6.QtCore import QObject, Signal, QMutex, QMutexLocker, Property as QProperty
from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt

from src import cacheManager
from src import universal as g
from src.innertube.song import Song

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
        if role == Qt.ItemDataRole.DisplayRole and index.isValid():
            return self._queue[index.row()].title
        if role == Qt.ItemDataRole.EditRole and index.isValid():
            return self._queue[index.row()]
        if role == Qt.ItemDataRole.UserRole + 1 and index.isValid():
            return self._queue[index.row()].artist
        if role == Qt.ItemDataRole.UserRole + 2 and index.isValid():
            return self._queue[index.row()].duration
        if role == Qt.ItemDataRole.UserRole + 3 and index.isValid():
            return "placeholder"
        if role == Qt.ItemDataRole.UserRole + 4 and index.isValid():
            return self._queue[index.row()].id
        if role == Qt.ItemDataRole.UserRole + 5 and index.isValid():
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
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return "Song"
            else:
                return f"Song {section}"
        return None
    
    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole and index.isValid():
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
    
    def insertRows(self, row, count):
        self.beginInsertRows(QModelIndex(), row, row + count - 1)
        self._queue.insert(row, [[] for _ in range(count)])
        self.endInsertRows()

class QueueManager(QObject):
    """Manages queue operations and selection"""
    
    queueChanged = Signal()
    currentSongChanged = Signal()
    pointerChanged = Signal()
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("QueueManager")
        self._pointer = 0
        self._queueAccessMutex = QMutex()
        self.queueModel = QueueModel()
        self.loop = LoopType.NONE
        self.purgetries = {}
        
        # Setup cache for queue persistence
        if not cacheManager.cacheExists("queueCache"):
            self.cache = cacheManager.CacheManager(name="queueCache")
        else:
            self.cache = cacheManager.getCache("queueCache")
    
    @QProperty(list, notify=queueChanged)
    def queue(self):
        with QMutexLocker(self._queueAccessMutex):
            return self.queueModel._queue
    
    @queue.setter
    def queue(self, value):
        with QMutexLocker(self._queueAccessMutex):
            self.setQueue(value, skipSetData=True)
            self.queueChanged.emit()
    
    @QProperty(list, notify=queueChanged)
    def queueIds(self):
        with QMutexLocker(self._queueAccessMutex):
            return self.queueModel._queueIds
    
    @QProperty(int, notify=pointerChanged)
    def pointer(self):
        return self._pointer
    
    @pointer.setter
    def pointer(self, value):
        if value == -1:
            # Special case for setting pointer to last song
            self._pointer = len(self.queue) - 1
        elif 0 <= value < len(self.queue):
            self._pointer = value
        else:
            raise ValueError("Pointer must be between 0 and length of queue")
        self.pointerChanged.emit()
        
    @QProperty(QObject, notify=currentSongChanged)
    def currentSong(self):
        if len(self.queue) > 0 and 0 <= self._pointer < len(self.queue):
            return self.queue[self._pointer]
        return None
    
    @QProperty(str, notify=currentSongChanged)
    def currentSongId(self):
        if len(self.queueIds) > 0 and 0 <= self._pointer < len(self.queueIds):
            return self.queueIds[self._pointer]
        return ""
    
    def info(self, pointer: int) -> Dict[str, str]:
        """Get info about song at specified position"""
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
    
    def setQueue(self, queue: list, skipSetData: bool = False):
        """Set the queue from a list of song IDs"""
        for item in queue:
            self.add(item)
    
    def add(self, id: str, index: int = -1, goto: bool = False):
        """Add a song to the queue"""
        s = Song(id=id)
        coro = s.get_info(g.asyncBgworker.API)
        future = asyncio.run_coroutine_threadsafe(coro, g.asyncBgworker.event_loop)
        future.result()  # Wait for the result
        g.bgworker.add_job(self.finishAdd, s, index, goto)
        
    def finishAdd(self, song: Song, index: int = -1, goto: bool = False):
        """Finish adding a song to the queue after info is loaded"""
        song.get_playback()
        if index == -1:
            self.queueModel.insertRows(len(self.queue), 1)
            self.queueModel.setData(self.queueModel.index(len(self.queue) - 1), song, Qt.EditRole)
            self.queueIds.append(song.id)
        else:
            self.queueModel.insertRows(index, 1)
            self.queueModel.setData(self.queueModel.index(index), song, Qt.EditRole)
            self.queueIds.insert(index, song.id)
            
        if goto:
            self.pointer = len(self.queue) - 1 if index == -1 else index
            self.currentSongChanged.emit()
    
    def moveNext(self) -> bool:
        """Move to next song in the queue based on loop settings"""
        if self._pointer >= len(self.queue) - 1:
            # End of queue
            if self.loop == LoopType.SINGLE:
                return True  # Same song again
            elif self.loop == LoopType.ALL:
                self.pointer = 0
                self.currentSongChanged.emit()
                return True
            else:
                # NONE - end of queue reached
                self.logger.info("Queue exhausted")
                return False
        else:
            # Move to next song
            self.pointer = self._pointer + 1
            self.currentSongChanged.emit()
            return True
    
    def movePrevious(self) -> bool:
        """Move to previous song in the queue"""
        if self._pointer > 0:
            self.pointer = self._pointer - 1
            self.currentSongChanged.emit()
            return True
        return False
    
    def clearQueue(self):
        """Clear the queue"""
        self.queueModel.setQueue([])
        self.queueIds = []
        self._pointer = 0
        self.queueChanged.emit()
