# stdlib imports
import json
import os
import pathlib
import random
import sys
import asyncio
import time
import typing
import urllib.parse
import inspect
import enum

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

class FwdVar:
    def __init__(self, getvar):
        self.var = getvar
        
    def __repr__(self):
        return self.var()
    
    def __str__(self):
        if isinstance(self.var(), str):
            return self.var()
        else:
            try:
                return str(self.var())
            except:
                return ""
            
class FakeQObj(QObject):
    def __init__(self, faking: object):
        super().__init__()
        self.using = faking
        usingCls = self.using.__class__
        
        inspected = inspect.getmembers(self.using)
        self.code: list[str] = inspect.getsource(usingCls).splitlines()
        
        for name, member in inspected:
            if name not in dir(QObject):
                if callable(member):
                    if isinstance(member, Property):
                        print("creating property " + name)
                        setattr(self, name, FwdVar(self.gvar(name)))
                    elif isinstance(member, Signal):
                        print("creating signal " + name)
                        self.createSignalAlias(name, member)
                    elif isinstance(member, Slot):
                        print("creating slot " + name)
                        setattr(self, name, self.funcforward(name))
                    else:
                        print("creaing function " + name)
                        setattr(self, name, self.funcforward(name))
                else:
                    try:
                        print("creating " + name, + member)
                    except:
                        print("creating " + name)
                    setattr(self, name, FwdVar(self.gvar(name)))
    
    def createSignalAlias(self, name, originalSignal: Signal):
        print("Creating signal alias for", name)

        # Complete Signal() code:
        # coolSignalName = Signal(str, "coolSignalName", ["arg1", "arg2"])
        
        # All are optional
        
        
        for index, line in enumerate(self.code):
            if line.strip().startswith("#"):
                continue
            
            if "Signal" in line and name in line:
                
                # Useful information in signals include the arguments, the type, and the name
                # The name is the easiest to get, as it's the name of the var, but the name in the signal is also important (QML uses it)
                
                sigline = line.strip()
                print(sigline)
                sigline = sigline[sigline.find("Signal"):]
                sigline = sigline.replace("Signal", "")
                sigline = sigline.lstrip("(").rstrip(")")
                sigline = sigline.split(",")
                

                sigtype = None
                signame = None
                sigargs = None
                
                if len(sigline) >= 1:
                    sigtype = sigline[0].strip()
                    # # Now we check if the parsed type is real
                    # try:
                    #     ev = eval("type(sigtype)")
                    #     if not isinstance(ev, object):
                    #         sigtype = None
                    # except:
                    #     sigtype = None
                    # Validation has been temporarily disabled because i need to fix the fact that imports exist, oops
                
                if len(sigline) >= 2:
                    signame = sigline[1].strip().removeprefix("\"").removesuffix("\"").removeprefix("\'").removesuffix("\'") # covers all cases
                if len(sigline) >= 3:
                    sigargs = sigline[2].strip()
                    if sigargs:
                        sigargs = json.loads(sigargs) # This is a list of strings
                        if not isinstance(sigargs, list):
                            sigargs = None
                            
        estr = "Signal("
        estr += sigtype if sigtype else ""
        estr += ", \"" + signame + "\"" if signame else ""
        estr += ", " + str(sigargs) if sigargs else ""
        estr += ")"
        
        aliasSignal = eval(estr)
        setattr(self.__class__, name, aliasSignal)
        originalSignal.connect(getattr(self, name).emit)
    
    def funcforward(self, name):
        def f(*args, **kwargs):
            return getattr(self.using, name)(*args, **kwargs)
        return f
    
    def gvar(self, name):
        def f():
            return getattr(self.using, name)
        return f
    
    def createPropGetter(self, name):
        def f():
            pass
        return f
    
    def createPropSetter(self, name):
        def f():
            pass
        return f

    @Property(str)
    def FAKE(self):
        return "FAKE"
    
    
    def __dir__(self):
        return dir(self.using)


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
    
    @Property(str, notify=songChanged)
    def currentSongId(self):
        return universal.queueInstance.currentSongId
    
    @Property(QObject, notify=songChanged)
    def currentSong(self):
        f = FakeQObj(universal.queueInstance.currentSongObject)
        
        return f
    
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