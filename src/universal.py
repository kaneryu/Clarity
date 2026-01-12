# flake8: noqa (Mostly just because of a lot of unused imports, imports not at the top, etc)
from src.misc.compiled import (
    __compiled__,
    compiled,
)
from src.misc.version import (
    version,
    release,
)
import threading
from hashlib import md5
import time
import builtins
from datetime import datetime, timezone
from typing import Union

import os
import logging
import sys
import json

print("Running with GIL", "disabled" if not sys._is_gil_enabled() else "enabled")


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
        skip = {
            "msg",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "exc_info",
            "exc_text",
            "stack_info",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
        }
        for k, v in record.__dict__.items():
            if k not in base and k not in skip:
                try:
                    json.dumps(v)
                    base[k] = v
                except TypeError:
                    base[k] = repr(v)
        return json.dumps(base, ensure_ascii=False)


class HumanReadableConsoleFormatter(logging.Formatter):
    base_keys = {"ts", "level", "logger", "msg", "module", "func", "line", "thread"}

    def __init__(self):
        super().__init__()
        self._json_formatter = JSONFormatter()

    def format(self, record: logging.LogRecord) -> str:
        try:
            data = json.loads(self._json_formatter.format(record))
        except Exception:
            return self._json_formatter.format(record)
        ts = data.get("ts", "?")
        level = data.get("level", "?")
        logger_name = data.get("logger", "?")
        func = data.get("func", "?")
        line = data.get("line", "?")
        msg = data.get("msg", "")
        # extras = [f"{k}={data[k]!r}" for k in data.keys() if k not in self.base_keys]
        # extras_str = (" " + " ".join(extras)) if extras else ""
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
logger = logging.getLogger("Clarity")
from .paths import Paths

os.environ["PATH"] = (
    (os.path.abspath(os.path.join(Paths.ASSETSPATH, "libs")))
    + os.pathsep
    + os.environ["PATH"]
)

from .workers import (
    bgworker,
    asyncBgworker,
    TimedJobSettings,
    argfuncFactory,
    asyncargfuncFactory,
)

bgworker.start()
asyncBgworker.start()

from .misc import settings as settings_module

settings = settings_module.Settings()

from src.cacheManager import (
    cacheManager as cacheManager_module,
    dataStore as dataStore_module,
)
import src.innertube as innertube_module
from src.innertube.globalModels import (
    NamespacedIdentifier,
    NamespacedTypedIdentifier,
    SimpleIdentifier,
)
from src.innertube import song as song_module
from src.innertube import album as album_module
from playback import queuemanager as queue_module


from src.network import NetworkManager, networkManager, OnlineStatus

from PySide6.QtCore import QThread, QMetaObject, Qt, Q_ARG, QResource

from .AppUrl import AppUrl, appUrl


from io import StringIO

from .misc import logHistoryManager
from .misc.enumerations.Search import SearchFilters

from src.qt import resources


mainThread: QThread = QThread.currentThread()


def ghash(thing):
    # print("making hash for", thing, ":", md5(str(thing).encode()).hexdigest())
    return md5(str(thing).encode()).hexdigest()


globalCache = cacheManager_module.CacheManager(
    name="cache", directory=os.path.join(Paths.DATAPATH, "cache")
)
songCache = cacheManager_module.CacheManager(
    name="songs_cache", directory=os.path.join(Paths.DATAPATH, "songs_cache")
)
imageCache = cacheManager_module.CacheManager(
    name="images_cache", directory=os.path.join(Paths.DATAPATH, "images_cache")
)
albumCache = cacheManager_module.CacheManager(
    name="albums_cache", directory=os.path.join(Paths.DATAPATH, "album_cache")
)
songDataStore = dataStore_module.DataStore(
    name="song_datastore", directory=os.path.join(Paths.DATAPATH, "song_datastore")
)

songDataStore.integrityCheck(True)
globalCache.integrityCheck()
songCache.integrityCheck()
imageCache.integrityCheck()


queueInstance: queue_module.Queue = queue_module.Queue()
search = innertube_module.search

searchModel = innertube_module.BasicSearchResultsModel()

mainThread: QThread = QThread.currentThread()


async def search_shorthand(
    query: str, ignore_spelling: bool = False
) -> Union[innertube_module.BasicSearchResultsModel, None]:
    searchModel.resetModel()
    return await innertube_module.search(
        query, filter=None, ignore_spelling=ignore_spelling, model=searchModel
    )


oldprint = builtins.print


def nprint(*args, **kwargs):
    mythread = threading.current_thread()
    time_ = time.strftime("%H:%M:%S")
    oldprint(time_, mythread, *args, **kwargs)
    return args


builtins.print = nprint

startupQueue: list[NamespacedTypedIdentifier] = [
    NamespacedTypedIdentifier.from_string("youtube:song:YPV676YeHNg"),
    NamespacedTypedIdentifier.from_string("youtube:song:a3mxLL7nX1E"),
    NamespacedTypedIdentifier.from_string("youtube:song:DimcNLjX50c"),
    NamespacedTypedIdentifier.from_string("youtube:song:r76AWibyDDQ"),
    NamespacedTypedIdentifier.from_string("youtube:song:fB8elptKFcQ"),
]


def getAllDownloadedSongs() -> list[NamespacedTypedIdentifier]:
    downloadedSongs: list[NamespacedTypedIdentifier] = []
    i: dataStore_module.DataStore
    j: str
    for i in dataStore_module.dataStores.values():
        if not i.tag == "songDonwnloads":
            continue
        for j in i.getAll().keys():
            try:
                if j.endswith("_downloadMeta"):
                    continue
                nsid = NamespacedTypedIdentifier.from_string(f"youtube:song:{j}")
                downloadedSongs.append(nsid)
            except Exception:
                logger.warning(f"Invalid downloaded song id in datastore: {j}")
    return downloadedSongs


def createSongMainThread(songId: NamespacedTypedIdentifier) -> song_module.Song:
    song = song_module.Song(songId)
    song.moveToThread(mainThread)
    return song


startupQueue.extend(i for i in getAllDownloadedSongs())
queueInstance.setQueue(startupQueue, False)
