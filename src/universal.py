from src.cacheManager import cacheManager as cacheManager_module
from src.innertube import song_queue as queue
from src.innertube import search as search_module
import threading
import asyncio
import types
from hashlib import md5
import time
import inspect
import versions
import os

from PySide6.QtCore import QThread

from .workers import BackgroundWorker, bgworker, asyncBgworker, Async_BackgroundWorker

from src.app.KImage import KImage, Placeholders, Status

version = versions.Version(open("version.txt").read().strip())
print("InnerTune version", version)

def ghash(thing):
    # print("making hash for", thing, ":", md5(str(thing).encode()).hexdigest())
    return md5(str(thing).encode()).hexdigest()

globalCache = cacheManager_module.CacheManager(name="cache")
songCache = cacheManager_module.CacheManager(name="songs_cache")
imageCache = cacheManager_module.CacheManager(name="images_cache")

queueInstance = queue.queue
search = search_module.search
searchModel = search_module.BasicSearchResultsModel()

mainThread: QThread = QThread.currentThread()

__compiled__ = False # will be set to true by nuitka

class Paths:
    assetsPath = os.path.abspath(os.path.join("assets") if __compiled__ else os.path.join("src", "app", "assets"))
    qmlPath = os.path.abspath(os.path.join("qml") if __compiled__ else os.path.join("src", "app", "qml"))
    rootpath = os.path.abspath(".")

print("assets path:", Paths.assetsPath)
print("qml path:", Paths.qmlPath)
print("root path:", Paths.rootpath)

async def search_shorthand(query: str, ignore_spelling: bool = False) -> search_module.BasicSearchResultsModel:
    return await search_module.search(query, ignore_spelling = ignore_spelling, model = searchModel)