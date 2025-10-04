import time
import logging
import traceback

from typing import Union, Any, cast

from PySide6.QtCore import Property as QProperty, Signal, Slot, Qt, QObject, QSize, QModelIndex, QPersistentModelIndex, QAbstractListModel, QMutex, QMutexLocker, QTimer

from src import universal as universal

from src.innertube.song import Song, SongProxy

class SongListModel(QAbstractListModel):
    songListChanged = Signal() 
    
    def __init__(self):
        super().__init__()
        self.__songList: list[Song] = []
        self._songList: list[Song]

    @QProperty(list)
    def _songList(self) -> list[Song]:
        return self.__songList
    
    @_songList.setter
    def _songList(self, value: list[Song]):
        self.__songList = value
        self.songListChanged.emit()
        
    
    def rowCount(self, parent=QModelIndex()):
        return len(self._songList)

    def count(self):
        return len(self._songList)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            return self._songList[index.row()].title
        if role == Qt.ItemDataRole.UserRole + 1:
            return self._songList[index.row()].artist
        if role == Qt.ItemDataRole.UserRole + 2:
            return self._songList[index.row()].duration
        if role == Qt.ItemDataRole.UserRole + 4:
            return self._songList[index.row()].id
        if role == Qt.ItemDataRole.UserRole + 5:
            return index.row()
        if role == Qt.ItemDataRole.UserRole + 6:
            return self._songList[index.row()]
        return None

    def roleNames(self):
        return {
            Qt.ItemDataRole.DisplayRole: b"title",
            Qt.ItemDataRole.UserRole + 1: b"artist",
            Qt.ItemDataRole.UserRole + 2: b"length",
            Qt.ItemDataRole.UserRole + 4: b"id",
            Qt.ItemDataRole.UserRole + 5: b"index",
            Qt.ItemDataRole.UserRole + 6: b"object",
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
            self._songList[index.row()] = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def setSongList(self, songList: list[Song]):
        self.beginResetModel()
        self._songList = songList
        self.endResetModel()

    def removeItem(self, index):
        if 0 <= index < len(self._songList):
            self.beginRemoveRows(QModelIndex(), index, index)
            del self._songList[index]
            self.endRemoveRows()

    def moveItem(self, from_index, to_index):
        if 0 <= from_index < len(self._songList) and 0 <= to_index < len(self._songList):
            self.beginMoveRows(QModelIndex(), from_index, from_index, QModelIndex(), to_index)
            self._songList.insert(to_index, self._songList.pop(from_index))
            self.endMoveRows()

    def insertRows(self, row: int, count: int = 1, parent: QModelIndex | QPersistentModelIndex = QModelIndex()):
        self.beginInsertRows(QModelIndex(), row, row + count - 1)
        self._songList.insert(row, [[] for _ in range(count)])  # type: ignore[arg-type]
        self.endInsertRows()
    
    def append(self, song: Song):
        self.beginInsertRows(QModelIndex(), len(self._songList), len(self._songList))
        self._songList.append(song)
        self.endInsertRows()

class SongProxyListModel(SongListModel):
    def __init__(self, parent: QObject | None = None):
        super().__init__()
        
        self._parent = parent
        self._proxyList: list[SongProxy] = []
        
        self.songListChanged.connect(self.updateProxyList)
        
    def updateProxyList(self):
        self._proxyList = [SongProxy(song, self) for song in self._songList]
        
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            return self._proxyList[index.row()].title
        if role == Qt.ItemDataRole.UserRole + 1:
            return self._proxyList[index.row()].artist
        if role == Qt.ItemDataRole.UserRole + 2:
            return self._proxyList[index.row()].duration
        if role == Qt.ItemDataRole.UserRole + 4:
            return self._proxyList[index.row()].id
        if role == Qt.ItemDataRole.UserRole + 5:
            return index.row()
        if role == Qt.ItemDataRole.UserRole + 6:
            return self._proxyList[index.row()]
        return None
    