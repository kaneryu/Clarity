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

from PySide6.QtCore import Signal as QSignal
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
class Backend(QObject):
    loadComplete = QSignal(name="loadComplete")
    activeTabChanged = QSignal(name="activeTabChanged")
    # tabModelChanged = QSignal(name="tabModelChanged")
    urlChanged = QSignal(name="urlChanged")
    _instance = None
    
    
    
    def __init__(self):
        super().__init__()
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self._value = 0
            
        self.queueModel_ = universal.queueInstance.queueModel
        self.fakequeue = Queue()
        
    @Property(str, notify=urlChanged)
    def url(self):
        return universal.appUrl.getUrl()
    
    @url.setter
    def url(self, value):
        try:
            urllib.parse.urlparse(value)
        except:
            print("Set URL failed, invalid URL", value)
            return
        universal.appUrl.setUrl(value)
        self.urlChanged.emit()
    
    @Property(dict, notify=urlChanged)
    def currentQuery(self):
        return universal.appUrl.getQuery()
    
    @Property(str, notify=urlChanged)
    def getCurrentPageFilePath(self):
        path = universal.appUrl.getPath()
        if path[0] == "page":
            if path == "/":
                ret = os.path.join(universal.Paths.qmlPath, "pages", "home.qml")
            else:
                first = path[1]
                first.replace("/", "")
                ret = os.path.join(universal.Paths.qmlPath, "pages", first + ".qml")
                
            if not os.path.exists(ret):
                print("Path does not exist", ret)
                return ""
            return "file:///" + ret
    
    @Slot(str)
    def setSearchURL(self, query):
        self.url = "innertune:///page/search?query=" + query
        
    @Slot(result=QObject)
    def getQM(self):
        return universal.queueInstance.queueModel
    
    @Property(QObject, constant=True)
    def queueModel(self):
        return self.queueModel_
    
    @Property(QObject, constant=True)
    def searchModel(self):
        return universal.searchModel
    
    @Slot(str, result=bool)
    def search(self, query: str) -> bool:
        universal.asyncBgworker.add_job_sync(func = universal.search_shorthand, usestar = False, a = [], kw = {"query": query})
        return True
    
    @Property(QObject, constant=True)
    def queue(self):
        return universal.queueInstance

    @Property(QObject, constant=True)
    def queueFunctions(self):
        return self.fakequeue
    
    @Slot(str, int)
    def queueCall(self, func, *args, **kwargs):
        f = getattr(universal.queue.Queue.getInstance(), func)
        universal.bgworker.jobs.append({"func": f, "args": args, "kwargs": kwargs})
    
    @Slot(str, result=str)
    def getPage(self, url: str) -> str:
        
        # parse the url
        # possible roots as of now:
        # page
        # then we have the page name after, so like page/home
        
        # pages are stored locally in the html folder (src/app/html)
        
        url = url.split("/")
        print(url)
        print("file:///" + os.path.join(os.path.dirname(__file__), "html", url[0], url[1], "index.html").replace("\\","/"))
        return "file:///" + os.path.join(os.path.dirname(__file__), "html", url[0], url[1], "index.html").replace("\\","/")
        
    @Slot(result=str)
    def ping(self) -> str:
        return "pong"
    
    @Slot(str, int, result=str)
    def roundImage(self, path, radius = 20) -> str:
        
        hsh = universal.ghash(path + "rounded" + str(radius))
        if universal.globalCache.scheckInCache(hsh): # check if the rounded image is cached
            return "file:///" + universal.imageCache.sgetKeyPath(hsh) # return the path of the image
        
        # check if source image is cached
        
        path = asyncio.run(downloadimage.downloadimage(path))
        hsh = asyncio.run(roundimage.roundimage(path, radius))
    
        return "file:///" + universal.imageCache.sgetKeyPath(hsh) # return the path of the image
                
        
    @Slot(str, int, int, result=str)
    def convertToCover(self, link: str, radius: str, size: int) -> str:
        return "file:///" + universal.imageCache.sgetKeyPath(asyncio.run(convertTocover.convertToCover(link=link, radius=radius, size=size)))
            