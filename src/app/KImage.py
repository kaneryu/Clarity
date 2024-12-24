from PySide6.QtCore import QUrl, Qt, QObject, Signal as QSignal, Slot as QSlot, Property as QProperty, QThread
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
    statusChanged = QSignal(str)
    imageChanged = QSignal(str)
    
    def __init__(self, placeholder: Placeholders = Placeholders.GENERIC, url: str = "", parent = None, deffered: bool = False):
        super().__init__(parent)
        self._placeholder = placeholder
        self._url = url
        self._image = None
        self._status = Status.INITIALIZING
        self.moveToThread(mainThread)
        
        if not deffered:
            self.beginDownload()
    
    @QSlot()
    def download(self):
        self.beginDownload()
        
    @QProperty(str, notify=imageChanged)
    def image(self):
        if not self.status == Status.DOWNLOADED:
            if self.status == Status.WAITING or self.status == Status.DOWNLOADING or Status.INITIALIZING:
                print("returning" + "file:///" + Placeholders.LOADING)
                return "file:///" + Placeholders.LOADING
            if self.status == Status.FAILED:
                print("returning" + "file://" + Placeholders.ERROR)
                return "file:///" + Placeholders.ERROR
        else:
            print("returning" + "file:///" + Placeholders.ERROR)
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
    
    async def imageDownload(self, url: str):
        self.status = Status.DOWNLOADING
        hash_ = cacheManager.ghash(url)
        
        if image := await cacheManager.getCache("images_cache").getKeyPath(hash_):
            self.status = Status.DOWNLOADED
            self.image = image
            return
        
        print("downloading image")
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
                await cacheManager.getCache("images_cache").put(key=hash_, value=temp, byte=True, filext=extension)
                
                self.status = Status.DOWNLOADED
            except Exception as e:

                self.status = Status.FAILED
        
        self.image = await cacheManager.getCache("images_cache").getKeyPath(hash_)
        
    async def imageDownloadFromId(self, id: str):
        api = asyncBgworker.API
        song_ = song.Song(id)
        await song_.get_info(api, cacheManager)
        self._url = song_.largestThumbailUrl
        self.beginDownload()
        
        
    def beginDownload(self):
        if image := cacheManager.getCache("images_cache").sgetKeyPath(cacheManager.ghash(self._url)):
            self.status = Status.DOWNLOADED
            self.image = image
            return
        
        asyncBgworker.add_job_sync(func=self.imageDownload, url=self._url)
        self.status = Status.WAITING