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
from PySide6.QtCore import Property as QProperty

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

class FakeSong(QObject):
    
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
        return self.target.id

    @id.setter
    def id(self, value: str) -> None:
        self.target.id = value

    @QProperty(str, notify=sourceChanged)
    def source(self) -> str:
        return self.target.source

    @source.setter
    def source(self, value: str) -> None:
        self.target.source = value

    @QProperty(bool, notify=downloadedChanged)
    def downloaded(self) -> bool:
        return self.target.downloaded

    @downloaded.setter
    def downloaded(self, value: bool) -> None:
        self.target.downloaded = value

    @QProperty(enum.Enum, notify=downloadStatusChanged)
    def downloadStatus(self) -> enum.Enum:
        return self.target.downloadStatus

    @downloadStatus.setter
    def downloadStatus(self, value: enum.Enum) -> None:
        self.target.downloadStatus = value

    @QProperty(int, notify=downloadProgressChanged)
    def downloadProgress(self) -> int:
        return self.target.downloadProgress

    @downloadProgress.setter
    def downloadProgress(self, value: int) -> None:
        self.target.downloadProgress = value
    
    
    @Slot()
    def test(self):
        print("test")
    
    