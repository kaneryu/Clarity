# stdlib imports
import random
import os
import pathlib
import random
import sys
import asyncio
import time
import typing
import urllib.parse

# library imports
from PySide6.QtCore import (
    QObject,
    Qt,
    QTimer,
    QThread,
)

from PySide6.QtCore import Signal as Signal
from PySide6.QtCore import Slot as Slot
from PySide6.QtQml import (
    QmlElement,
    QmlSingleton,
    QQmlApplicationEngine,
    qmlRegisterSingletonInstance,
    qmlRegisterSingletonType,
)
from PySide6.QtCore import Property


from src.app.pyutils import (roundimage, downloadimage, convertTocover)
import src.universal as universal

QML_IMPORT_NAME = "CreateTheSun"
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0

class Queue(QObject):
    def __init__(self):
        """A fake queue class that will call the real one in the other thread.
        """
        super().__init__()
        pass

    @Slot(str)
    def playSong(self, id: str):
        f = universal.queue.Queue.getInstance().playSong
        universal.bgworker.jobs.append({"func": f, "args": [], "kwargs": {"id": id}})

    @Slot()
    def pause(self):
        f = universal.queue.Queue.getInstance().pause
        universal.bgworker.jobs.append({"func": f, "args": [], "kwargs": {}})

    @Slot()
    def play(self):
        f = universal.queue.Queue.getInstance().play
        universal.bgworker.jobs.append({"func": f, "args": [], "kwargs": {}})

    @Slot()
    def stop(self):
        f = universal.queue.Queue.getInstance().stop
        universal.bgworker.jobs.append({"func": f, "args": [], "kwargs": {}})

    @Slot()
    def reload(self):
        f = universal.queue.Queue.getInstance().reload
        universal.bgworker.jobs.append({"func": f, "args": [], "kwargs": {}})

    @Slot(int)
    def setPointer(self, index: int):
        f = universal.queue.Queue.getInstance().setPointer
        universal.bgworker.jobs.append({"func": f, "args": [index], "kwargs": {}})

    @Slot()
    def next(self):
        f = universal.queue.Queue.getInstance().next
        universal.bgworker.jobs.append({"func": f, "args": [], "kwargs": {}})

    @Slot()
    def prev(self):
        f = universal.queue.Queue.getInstance().prev
        universal.bgworker.jobs.append({"func": f, "args": [], "kwargs": {}})

    def info(self, pointer: int):
        f = universal.queue.Queue.getInstance().info
        universal.bgworker.jobs.append({"func": f, "args": [pointer], "kwargs": {}})

    @Slot(str, int)
    def add(self, link: str, index: int):
        f = universal.queue.Queue.getInstance().add
        universal.bgworker.jobs.append({"func": f, "args": [link, index], "kwargs": {}})
    
    @Slot(str)
    def addEnd(self, link: str):
        f = universal.queue.Queue.getInstance().add
        universal.bgworker.jobs.append({"func": f, "args": [link], "kwargs": {}})
        
    @Slot(str, int)
    def addId(self, id: str, index: int):
        f = universal.queue.Queue.getInstance().add_id
        universal.bgworker.jobs.append({"func": f, "args": [id, index], "kwargs": {}})

    @Slot(str)
    def addIdEnd(self, id: str):
        f = universal.queue.Queue.getInstance().add_id
        universal.bgworker.jobs.append({"func": f, "args": [id], "kwargs": {}})
    
    @Slot(int)
    def seek(self, time: int):
        f = universal.queue.Queue.getInstance().seek
        universal.bgworker.jobs.append({"func": f, "args": [time], "kwargs": {}})

    @Slot(int)
    def aseek(self, time: int):
        f = universal.queue.Queue.getInstance().aseek
        universal.bgworker.jobs.append({"func": f, "args": [time], "kwargs": {}})

    @Slot(int)
    def pseek(self, percentage: int):
        f = universal.queue.Queue.getInstance().pseek
        universal.bgworker.jobs.append({"func": f, "args": [percentage], "kwargs": {}})

@QmlElement
class Interactions(QObject):
    _instance = None
    songChanged = Signal()
    playingStatusChanged = Signal()
    def __init__(self):
        super().__init__()
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self._value = 0
            
        self.queueModel_ = universal.queueInstance.queueModel
        self.fakequeue = Queue()
        
        self._currentSongCover = universal.KImage(placeholder=universal.Placeholders.GENERIC, deffered=True, cover=True, radius=10)
        universal.queueInstance.songChanged.connect(self.changeSongKImage)
        universal.queueInstance.songChanged.connect(self.songChangeMirror)
        universal.queueInstance.playingStatusChanged.connect(self.playingStatusChanged.emit)
        
    @Slot(str)
    def songChangeMirror(self):
        print("Interactions knows the song changed")
        self.songChanged.emit()
    
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
        return universal.queueInstance.currentSongTitle
    
    @Property(str, notify=songChanged)
    def currentSongChannel(self):
        return universal.queueInstance.currentSongChannel

    @Property(int, notify=songChanged)
    def currentSongTime(self):
        return universal.queueInstance.currentSongTime
    
    @Property(int, notify=songChanged)
    def currentSongDuration(self):
        return universal.queueInstance.currentSongDuration
    
    @Property(str, notify=songChanged)
    def songFinishesAt(self):
        return universal.queueInstance.songFinishesAt
    
    @Property(bool, notify=songChanged)
    def currentSongId(self):
        return universal.queueInstance.currentSongId
    
    @Property(bool, notify=playingStatusChanged)
    def isPlaying(self):
        return universal.queueInstance.isPlaying
    

    
    @Slot(str)
    def searchPress(self, id: str):
        q = universal.queueInstance
        q.add(id)
        q.goToSong(id)
    
    @Slot(int)
    def seekPercent(self, percentage: int):
        q = universal.queueInstance
        q.pseek(percentage)
        
        
    @Slot()
    def next(self):
        q = universal.queueInstance
        q.next()
        print("next")
    
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

    