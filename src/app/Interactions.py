# stdlib imports
import json
import inspect
from typing import overload

# library imports
from PySide6.QtCore import (
    QObject,
)

from PySide6.QtCore import Signal as Signal
from PySide6.QtCore import Slot as Slot, QMetaObject, Qt, QMutexLocker, QMutex
from PySide6.QtQml import (
    QmlElement,
)
from PySide6.QtCore import Property

import src.universal as universal
from . import Interfaces

QML_IMPORT_NAME = "CreateTheSun"
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0

class loggingMutexLocker(QMutexLocker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def __enter__(self):
        print("waiting for lock & executing")
        super().__enter__()
    
    def __exit__(self, *args):
        print("unlocked")
        super().__exit__(*args)



@QmlElement
class Interactions(QObject):
    _instance = None
    songChanged = Signal()
    playingStatusChanged = Signal()
    durationChanged = Signal()
    def __init__(self):
        super().__init__()
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self._value = 0
            
        self.queueModel_ = universal.queueInstance.queueModel
        
        self._currentSongCover = universal.KImage(placeholder=universal.Placeholders.GENERIC, deffered=True, cover=True, radius=50)
        self._currentSongCover.setParent(self)
        self._currentSongCover.imageChanged.connect(self.coverChangedTest)
        universal.queueInstance.songChanged.connect(self.changeSongKImage)
        universal.queueInstance.songChanged.connect(self.songChangeMirror)
        universal.queueInstance.playingStatusChanged.connect(self.playingStatusMirror)
        universal.queueInstance.durationChanged.connect(self.durationChangedMirror)
    
    def playingStatusMirror(self):
        self.playingStatusChanged.emit()
    
    def coverChangedTest(self):
        print("cover changed")

    @Slot()
    def songChangeMirror(self):
        self.songChanged.emit()
        self.durationChanged.emit()
    
    @Slot()
    def durationChangedMirror(self):
        self.durationChanged.emit()
    
    @Slot(str)
    def changeSongKImage(self):
        print("changing song kimage")
        id = universal.queueInstance.currentSongId
        self._currentSongCover.setId(id)

    @Property(QObject, constant=True)
    def currentSongCover(self):
        return self._currentSongCover
    
    @Property(str, notify=songChanged)
    def currentSongTitle(self):
        with QMutexLocker(universal.queueInstance._mutex):
            return universal.queueInstance.currentSongTitle
    
    @Property(str, notify=songChanged)
    def currentSongChannel(self):
        with QMutexLocker(universal.queueInstance._mutex):
            return universal.queueInstance.currentSongChannel

    @Property(int, notify=songChanged)
    def currentSongTime(self):
        with QMutexLocker(universal.queueInstance._mutex):
            return universal.queueInstance.currentSongTime
    
    @Property(int, notify=durationChanged)
    def currentSongDuration(self):
        with QMutexLocker(universal.queueInstance._mutex):
            return universal.queueInstance.currentSongDuration
    
    @Property(str, notify=songChanged)
    def songFinishesAt(self):
        with QMutexLocker(universal.queueInstance._mutex):
            return universal.queueInstance.songFinishesAt
    
    @Property(str, notify=songChanged)
    def currentSongId(self):
        with QMutexLocker(universal.queueInstance._mutex):
            return universal.queueInstance.currentSongId
    
    @Property(QObject, notify=songChanged)
    def currentSong(self):
        f: universal.song_module.Song = universal.song_module.SongProxy(universal.queueInstance.currentSongObject, self)
        return f
    
    @Property(bool, notify=playingStatusChanged)
    def isPlaying(self):
        return universal.queueInstance.isPlaying

    @Property(int, notify=playingStatusChanged)
    def playingStatus(self):
        return int(universal.queueInstance.playingStatus)
    
    
    @Slot(str)
    def searchPress(self, id: str):
        q = universal.queueInstance
        print("searchPress", id)
        q.add(id, goto=True)
    
    @Slot(int)
    def seekPercent(self, percentage: int):
        q = universal.queueInstance
        q.pseek(percentage)
        
        
    @Slot()
    def next(self):
        q = universal.queueInstance
        q.next()

    @Slot(int)
    def setQueueIndex(self, index: int):
        q = universal.queueInstance
        q.setPointer(index)
    
    @Slot()
    def back(self):
        q = universal.queueInstance
        q.prev()
        
    @Slot()
    def togglePlayback(self):
        q = universal.queueInstance
        if q.isPlaying:
            q.pause()
        else:
            q.resume()
    
    @Slot(str)
    def downloadSong(self, id: str):
        smodule = universal.song_module
        song = smodule.Song(id)
        universal.asyncBgworker.add_job_sync(song.download)
    
    @Slot(str, result=QObject)
    def getSong(self, id: str):
        smodule = universal.song_module
        song = smodule.SongProxy(smodule.Song(id), self)
        return song

    @Slot(QObject, result=QObject)
    def getSongCover(self, song: universal.song_module.Song) -> QObject:
        i = universal.KImage(placeholder=universal.Placeholders.GENERIC, deffered=True, cover=True, radius=50)
        i.setId(song.id)
        i.beginDownload()
        return i
    
    @Slot(str, result=QObject)
    def getSongCoverId(self, arg: str) -> QObject:
        i = universal.KImage(placeholder=universal.Placeholders.GENERIC, deffered=True, cover=True, radius=50)
        i.setId(arg)
        i.beginDownload()
        return i
    
    # convenience functions for interacting with the song class
    # all functions will take in an ID
    @Slot(str)
    def getSongDownloadStatus(self, id: str):
        smodule = universal.song_module
        song = smodule.Song(id)
        return song.downloadStatus
    
    @Slot(str)
    def getSongDownloadProgress(self, id: str):
        smodule = universal.song_module
        song = smodule.Song(id)
        return song.downloadProgress