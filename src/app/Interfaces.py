"""This module contains the interfaces for the QML objects to interact with the Python objects.
These are read only interfaces, and may not implement all functions (thoguh they should implement all properties).

You should be able to use the objects direcly in python as it seems that python interacts with different-threaded QObjects just fine.
"""

# stdlib imports
import json
import inspect
import enum

# library imports
from PySide6.QtCore import (
    QObject,
)

from PySide6.QtCore import Signal as Signal
from PySide6.QtCore import Slot as Slot
from PySide6.QtQml import (
    QmlElement,
)
from PySide6.QtCore import Property as QProperty, QMetaMethod, QMetaObject, Qt, QAbstractListModel

import src.universal as universal

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
            

class SongProxy(QObject):
    idChanged = Signal(str)
    sourceChanged = Signal(str)
    downloadedChanged = Signal(bool)
    downloadStatusChanged = Signal(enum.Enum)
    downloadProgressChanged = Signal(int)
    
    def __init__(self, target: universal.song_module.Song, parent: QObject) -> None:
        super().__init__()
        self.target = target
        
        self.target.idChanged.connect(self.idChanged)
        self.target.sourceChanged.connect(self.sourceChanged)
        self.target.downloadedChanged.connect(self.downloadedChanged)
        self.target.downloadStatusChanged.connect(self.downloadStatusChanged)
        self.target.downloadProgressChanged.connect(self.downloadProgressChanged)
        
        self.target.idChanged.connect(lambda: self.update("id"))
        self.target.sourceChanged.connect(lambda: self.update("source"))
        self.target.downloadedChanged.connect(lambda: self.update("downloaded"))
        self.target.downloadStatusChanged.connect(lambda: self.update("downloadStatus"))
        self.target.downloadProgressChanged.connect(lambda: self.update("downloadProgress"))
        
        self._id = self.target.id
        self._source = self.target.source
        self._downloaded = self.target.downloaded
        self._downloadStatus = self.target.downloadStatus
        self._downloadProgress = self.target.downloadProgress
        
        
        
        self.moveToThread(universal.mainThread)
        self.setParent(parent)

                    
    def createPropGetter(self, name):
        def getter(self):
            return getattr(self.target, name)
        return getter
    
    def createPropSetter(self, name):
        def setter(value):
            setattr(self.target, name, value)
        return setter
    
    def __getattr__(self, name):
        # Forward any unknown attribute access to target
        return getattr(self.target, name)
    
    @QProperty(str, constant=True)
    def title(self) -> str:
        return self.target.title
    
    @QProperty(str, constant=True)
    def artist(self) -> str:
        return self.target.artist
    
    @QProperty(str, constant=True)
    def description(self) -> str:
        return self.target.description
    
    @QProperty(str, constant=True)
    def uploadDate(self) -> str:
        return self.target.uploadDate
    
    @QProperty(str, constant=True)
    def views(self) -> str:
        return self.target.views
        
    @QProperty(str, notify=idChanged)
    def id(self) -> str:
        return self._id

    @QProperty(str, notify=sourceChanged)
    def source(self) -> str:
        return self._source

    @QProperty(bool, notify=downloadedChanged)
    def downloaded(self) -> bool:
        return self._downloaded

    @QProperty(enum.Enum, notify=downloadStatusChanged)
    def downloadStatus(self) -> enum.Enum:
        return self._downloadStatus

    @QProperty(int, notify=downloadProgressChanged)
    def downloadProgress(self) -> int:
        return self._downloadProgress
    
    @Slot()
    def test(self):
        print("test")
    
    def update(self, name):
        setattr(self, "_"+name, getattr(self.target, name))
        exec("self."+name+"Changed.emit(getattr(self, '_"+name+"'))")
        print("updating", name, "to", getattr(self, "_"+name))

class KImageProxy(QObject):
    imageChanged = Signal(str)
    statusChanged = Signal(str)
    def __init__(self, target: universal.KImage, parent: QObject) -> None:
        super().__init__()
        self.target = target
        self.target.imageChanged.connect(self.imageChanged)
        self.target.statusChanged.connect(self.statusChanged)
        
        self._image = self.target.image
        self._status = self.target.status
        
        self.target.imageChanged.connect(lambda: self.update("image"))
        self.target.statusChanged.connect(lambda: self.update("status"))
        
        self.moveToThread(universal.mainThread)
        self.setParent(parent)
    
    def update(self, name):
        setattr(self, "_"+name, getattr(self.target, name))
        exec("self."+name+"Changed.emit(getattr(self, '_"+name+"'))")
        print("updating", name, "to", getattr(self, "_"+name))
    
    @QProperty(str, notify=imageChanged)
    def image(self):
        return self._image
    
    @QProperty(str, notify=statusChanged)
    def status(self):
        return self._status
    
