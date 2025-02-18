from PySide6.QtCore import QUrl, Qt, QObject, Signal, Slot, Property as QProperty, QThread
import httpx
import os
import mimetypes

from enum import StrEnum
import requests
import asyncio

import src.cacheManager as cacheManager
from src.workers import asyncBgworker, mainThread
from src.innertube import song

__compiled__ = False

class Paths:
    assetsPath = os.path.abspath(os.path.join("assets") if __compiled__ else os.path.join("src", "app", "assets"))
    qmlPath = os.path.abspath(os.path.join("qml") if __compiled__ else os.path.join("src", "app", "qml"))
    rootpath = os.path.abspath(".")



class Placeholders(StrEnum):
    """A list of placeholders that can be used for the image.
    """
    SONG = os.path.join(Paths.assetsPath, "placeholders", "song.png")
    ARTIST = os.path.join(Paths.assetsPath, "placeholders", "artist.png")
    ALBUM = os.path.join(Paths.assetsPath, "placeholders", "album.png")
    PLAYLIST = os.path.join(Paths.assetsPath, "placeholders", "playlist.png")
    USER = os.path.join(Paths.assetsPath, "placeholders", "user.png")
    
    GENERIC = os.path.join(Paths.assetsPath, "placeholders", "generic.png")
    
    ERROR = os.path.join(Paths.assetsPath, "placeholders", "error.png")
    LOADING = os.path.join(Paths.assetsPath, "placeholders", "loading.png")

class Status(StrEnum):
    INITIALIZING = "init"
    
    DOWNLOADING = "dl"
    DOWNLOADED = "dlf"
    
    FAILED = "fail"
    WAITING = "wait"

class KImage(QObject):
    """An image object that downloads the image in another thread, making a placeholder available immediately.
    """
    statusChanged = Signal(str)
    imageChanged = Signal(str)
    
    _instances = {}
    
    # def __new__(cls, placeholder: Placeholders = Placeholders.GENERIC, url: str = "", parent = None, deffered: bool = False, cover: bool = False, radius: int = 10) -> "KImage":
    #     if url in cls._instances:
    #         return cls._instances[url]
    #     instance = super(KImage, cls).__new__(cls, placeholder, url, parent, deffered, cover, radius)
    #     cls._instances[url] = instance
    #     return instance
        
    def __init__(self, placeholder: Placeholders = Placeholders.GENERIC, url: str = "", parent = None, deffered: bool = False, cover: bool = False, radius: int = 10):
        super().__init__(parent)
        
        # if hasattr(self, "_init"):
        #    return
        
        # self._init = True
        self._placeholder = placeholder
        self._url = url
        self._image = None
        self._status = Status.INITIALIZING
        # self.moveToThread(mainThread)
        
        self.cover = cover
        self.images_cache = cacheManager.getCache("images_cache")
        self.radius = radius
        
        if not deffered:
            self.beginDownload()
        
    @Slot()
    def download(self):
        self.beginDownload()
        
    @QProperty(str, notify=imageChanged)
    def image(self):
        if not self.status == Status.DOWNLOADED:
            if self.status == Status.WAITING or self.status == Status.DOWNLOADING or self.status == Status.INITIALIZING:
                return "file:///" + Placeholders.LOADING
            if self.status == Status.FAILED:
                return "file:///" + Placeholders.ERROR
        else:
            return "file:///" + self._image
    
    @image.setter
    def image(self, value: str):
        """should NOT contain the file:/// prefix

        Args:
            value (str): the path to the image, WITHOUT the file:/// prefix
        """
        self._image = value
        self.imageChanged.emit(self._image)
        
    @QProperty(str, notify=statusChanged)
    def status(self):
        return self._status

    @status.setter
    def status(self, value: str):
        self._status = value
        self.statusChanged.emit(self._status)
    
    async def imageDownload(self, url: str = "", id: str = ""):
        if id:
            api = asyncBgworker.API
            song_: song.Song = song.Song(id)
            await song_.get_info(api)
            url = song_.largestThumbailUrl
            
        if not id and not url:
            self.status = Status.FAILED
            return
            
        self.status = Status.DOWNLOADING
        hash_ = cacheManager.ghash(url)
        
        if not self.cover:
            if image := self.images_cache.getKeyPath(hash_):
                self.status = Status.DOWNLOADED
                self.image = image
                return
        else:
            if image := self.images_cache.getKeyPath(hash_ + "coverconvertedrounded"):
                self.image = image
                return
        
        if not (self.cover and self.images_cache.getKeyPath(hash_)):
            # if we're in cover mode and the image is downloaded, skip this step.
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(url)
                    response.raise_for_status()
                    temp = response.content
                    content_type = response.headers.get("Content-Type")
                    if content_type:
                        extension = mimetypes.guess_extension(content_type)
                    else:
                        extension
                    self.images_cache.put(key=hash_, value=temp, byte=True, filext=extension)
                    
                    self.status = Status.DOWNLOADED
                except Exception as e:

                    self.status = Status.FAILED
        
        if self.cover:
            if image := self.images_cache.getKeyPath(hash_ + "coverconverted"):
                self.image = image
                return # return if the image is already converted, and in the cache
            
            image = self.images_cache.getKeyPath(hash_)
            image = await asyncBgworker.putCoverConvert(callback=self.coverCallback, path=image, radius=self.radius, size=100, identify=hash_ + "coverconverted")
        else:
            self.image = self.images_cache.getKeyPath(hash_)
        
    def coverCallback(self, path: str):
        self.image = self.images_cache.getKeyPath(path)
    
    def setRadius(self, radius: int):
        self.radius = radius
    
    def setId(self, id: str):
        self.beginDownload(id=id)
        
    
    def beginDownload(self, url: str = "", id: str = ""):
        if url:
            self._url = url
        
        identifier = id if id else self._url
        if image := self.images_cache.getKeyPath(cacheManager.ghash(identifier)):
            self.status = Status.DOWNLOADED
            self.image = image
            return
        
        asyncBgworker.add_job_sync(func=self.imageDownload, url=self._url, id=id)
        self.status = Status.WAITING
        
class KImageProxy(QObject):
    imageChanged = Signal(str)
    statusChanged = Signal(str)
    def __init__(self, target: KImage, parent: QObject) -> None:
        super().__init__()
        self.target = target
        self.target.imageChanged.connect(self.imageChanged)
        self.target.statusChanged.connect(self.statusChanged)
        
        self._image = self.target.image
        self._status = self.target.status
        
        self.target.imageChanged.connect(lambda: self.update("image"))
        self.target.statusChanged.connect(lambda: self.update("status"))
        
        self.moveToThread(mainThread)
        self.setParent(parent)
    
    def update(self, name):
        setattr(self, "_"+name, getattr(self.target, name))
        exec("self."+name+"Changed.emit(getattr(self, '_"+name+"'))")
    
    @QProperty(str, notify=imageChanged)
    def image(self):
        return self._image
    
    @QProperty(str, notify=statusChanged)
    def status(self):
        return self._status