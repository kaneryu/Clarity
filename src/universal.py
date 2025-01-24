from src.cacheManager import cacheManager as cacheManager_module, dataStore as dataStore_module
import src.innertube as innertube_module
from src.innertube import search as search_module
from src.innertube import song as song_module
import threading
import asyncio
import types
from hashlib import md5
import time
import builtins
import versions
import os

from PySide6.QtCore import QThread

from .workers import BackgroundWorker, bgworker, asyncBgworker, Async_BackgroundWorker

from src.app.KImage import KImage, Placeholders, Status, KImageProxy
from .AppUrl import AppUrl, appUrl

try:
    with open("version.txt") as f:
        version = versions.Version(f.read().strip())
except FileNotFoundError:
    print("version.txt not found, using 0.0.0")
    version = versions.Version("0.0.0")
    
print("InnerTune version", version)
# input()

def ghash(thing):
    # print("making hash for", thing, ":", md5(str(thing).encode()).hexdigest())
    return md5(str(thing).encode()).hexdigest()


datapath = os.path.abspath("data")
globalCache = cacheManager_module.CacheManager(name="cache", directory=os.path.join(datapath, "cache"))
songCache = cacheManager_module.CacheManager(name="songs_cache", directory=os.path.join(datapath, "songs_cache"))
imageCache = cacheManager_module.CacheManager(name="images_cache", directory=os.path.join(datapath, "images_cache"))

asyncBgworker.add_job_sync(globalCache.collect)
asyncBgworker.add_job_sync(songCache.collect)
asyncBgworker.add_job_sync(imageCache.collect)

songDataStore = dataStore_module.DataStore(name="song_datastore", directory=os.path.join(datapath, "song_datastore"))

songDataStore.integrityCheck()
globalCache.integrityCheck()
songCache.integrityCheck()
imageCache.integrityCheck()

song_module.DATASTORE_MODULE = dataStore_module
song_module.CACHEMANAGER_MODULE = cacheManager_module

queueInstance: innertube_module.Queue = innertube_module.Queue()
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



oldprint = builtins.print
def nprint(*args, **kwargs):
    mythread = threading.current_thread()
    time_  = time.strftime("%H:%M:%S")
    oldprint(time_, mythread, *args, **kwargs)
    return args
builtins.print = nprint

startupQueue = ["YPV676YeHNg", "a3mxLL7nX1E", "DimcNLjX50c", "r76AWibyDDQ", "fB8elptKFcQ"]
def getAllDownloadedSongs() -> list:
    l = list(songDataStore.getAll().keys())
    l = [i for i in l if not i.endswith("_downloadMeta")]
    return l

startupQueue.extend(i for i in getAllDownloadedSongs())
bgworker.add_job(queueInstance.setQueue, startupQueue)
