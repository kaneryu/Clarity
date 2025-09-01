import versions
try:
    with open("version.txt") as f:
        version = versions.Version(f.read().strip())
except FileNotFoundError:
    print("version.txt not found, using 0.0.0")
    version = versions.Version("0.0.0")
    
print("Clarity", repr(version))


import threading
import concurrent.futures
import types
from hashlib import md5
import time
import builtins
from datetime import datetime, timezone

import os
import logging
import json

class JSONFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, timezone.utc)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat(timespec="milliseconds") + "Z"

    def format(self, record: logging.LogRecord) -> str:
        base = {
            "ts": self.formatTime(record, datefmt="%H:%M:%S.%fZ"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "module": record.module,
            "func": record.funcName,
            "line": record.lineno,
            "thread": record.threadName,
        }
        skip = {"msg","levelname","levelno","pathname","filename","module","exc_info","exc_text","stack_info","lineno","funcName","created","msecs","relativeCreated","thread","threadName","processName","process"}
        for k, v in record.__dict__.items():
            if k not in base and k not in skip:
                try:
                    json.dumps(v)
                    base[k] = v
                except TypeError:
                    base[k] = repr(v)
        return json.dumps(base, ensure_ascii=False)

class HumanReadableConsoleFormatter(logging.Formatter):
    base_keys = {"ts","level","logger","msg","module","func","line","thread"}
    def __init__(self):
        super().__init__()
        self._json_formatter = JSONFormatter()
    def format(self, record: logging.LogRecord) -> str:
        try:
            data = json.loads(self._json_formatter.format(record))
        except Exception:
            return self._json_formatter.format(record)
        ts = data.get("ts","?")
        level = data.get("level","?")
        logger_name = data.get("logger","?")
        func = data.get("func","?")
        line = data.get("line","?")
        msg = data.get("msg","")
        extras = [f"{k}={data[k]!r}" for k in data.keys() if k not in self.base_keys]
        extras_str = (" " + " ".join(extras)) if extras else ""
        return f"[{ts}] {level:<8} {logger_name}.{func}:{line} | {msg}"

def install_json_logging(level=logging.INFO):
    root = logging.getLogger()
    # Always replace existing stream handlers with our human readable one
    for h in list(root.handlers):
        if isinstance(h, logging.StreamHandler):
            root.removeHandler(h)
    handler = logging.StreamHandler()
    handler.setFormatter(HumanReadableConsoleFormatter())
    root.addHandler(handler)
    root.setLevel(level)

install_json_logging()

from src.cacheManager import cacheManager as cacheManager_module, dataStore as dataStore_module
import src.innertube as innertube_module
from src.innertube import search as search_module
from src.innertube import song as song_module

from src.network import NetworkManager, networkManager, is_internet_connected, connected as internet_connected

from PySide6.QtCore import QThread, QMetaObject, Qt, Q_ARG

from .workers import BackgroundWorker, bgworker, asyncBgworker, Async_BackgroundWorker

from .AppUrl import AppUrl, appUrl

from .misc import settings as settings_module

from io import StringIO

from .misc import logHistoryManager

mainThread: QThread = QThread.currentThread()

settings = settings_module.Settings()

def ghash(thing):
    # print("making hash for", thing, ":", md5(str(thing).encode()).hexdigest())
    return md5(str(thing).encode()).hexdigest()


datapath = os.path.abspath("data")
globalCache = cacheManager_module.CacheManager(name="cache", directory=os.path.join(datapath, "cache"))
songCache = cacheManager_module.CacheManager(name="songs_cache", directory=os.path.join(datapath, "songs_cache"))
imageCache = cacheManager_module.CacheManager(name="images_cache", directory=os.path.join(datapath, "images_cache"))
queueCache = cacheManager_module.CacheManager(name="queue_cache", directory=os.path.join(datapath, "queue_cache"))
songDataStore = dataStore_module.DataStore(name="song_datastore", directory=os.path.join(datapath, "song_datastore"))

songDataStore.integrityCheck(True)
globalCache.integrityCheck()
songCache.integrityCheck()
imageCache.integrityCheck()


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
    return await search_module.search(query, filter = search_module.searchFilters.SONGS, ignore_spelling = ignore_spelling, model = searchModel)



oldprint = builtins.print
def nprint(*args, **kwargs):
    mythread = threading.current_thread()
    time_  = time.strftime("%H:%M:%S")
    oldprint(time_, mythread, *args, **kwargs)
    return args
builtins.print = nprint

startupQueue: list[str] = ["YPV676YeHNg", "a3mxLL7nX1E", "DimcNLjX50c", "r76AWibyDDQ", "fB8elptKFcQ"]
def getAllDownloadedSongs() -> list:
    l = list(songDataStore.getAll().keys())
    l = [i for i in l if not i.endswith("_downloadMeta")]
    return l

# def runInMainThread(func, *args, **kwargs):
#     if threading.current_thread() == mainThread:
#         return func(*args, **kwargs)
#     f = mainThreadExcecutor.submit(lambda: func(*args, **kwargs))
#     return f.result()

def createSongMainThread(songId: str) -> song_module.Song:
    song = song_module.Song(songId)
    song.moveToThread(mainThread)
    return song

startupQueue.extend(i for i in getAllDownloadedSongs())
queueInstance.setQueue(startupQueue, False)


# is_internet_connected()