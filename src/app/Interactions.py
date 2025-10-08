# stdlib imports
import json
import logging
from typing import overload

# library imports
from PySide6.QtCore import (
    QObject,
)

from PySide6.QtCore import Signal as Signal
from PySide6.QtCore import Slot as Slot, QMetaObject, Qt, QMutexLocker, QMutex
from PySide6.QtQml import (
    QmlElement,
)
from PySide6.QtCore import Property

import src.universal as universal
import src.misc.enumerations.Song as song_enums

QML_IMPORT_NAME = "CreateTheSun"
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


class loggingMutexLocker(QMutexLocker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __enter__(self):
        print("waiting for lock & executing")
        super().__enter__()

    def __exit__(self, *args):
        print("unlocked")
        super().__exit__(*args)


@QmlElement
class Interactions(QObject):
    _instance = None
    songChanged = Signal()
    playingStatusChanged = Signal()
    durationChanged = Signal()

    def __init__(self):
        super().__init__()
        if not hasattr(self, "initialized"):
            self.initialized = True
            self._value = 0

        self.queueModel_ = universal.queueInstance.queueModel

        universal.queueInstance.songChanged.connect(self.songChangeMirror)
        universal.queueInstance.playingStatusChanged.connect(self.playingStatusMirror)
        universal.queueInstance.durationChanged.connect(self.durationChangedMirror)

        self.logger = logging.getLogger("Interactions")

    def playingStatusMirror(self):
        self.playingStatusChanged.emit()

    @Slot()
    def songChangeMirror(self):
        self.songChanged.emit()
        self.durationChanged.emit()

    @Slot()
    def durationChangedMirror(self):
        self.durationChanged.emit()

    @Property(str, notify=songChanged)
    def currentSongTitle(self):
        # with QMutexLocker(universal.queueInstance._mutex):
        return universal.queueInstance.currentSongTitle

    @Property(str, notify=songChanged)
    def currentSongChannel(self):
        with QMutexLocker(universal.queueInstance._mutex):
            return universal.queueInstance.currentSongChannel

    @Property(int, notify=songChanged)
    def currentSongTime(self):
        with QMutexLocker(universal.queueInstance._mutex):
            return universal.queueInstance.currentSongTime

    @Property(int, notify=durationChanged)
    def currentSongDuration(self):
        with QMutexLocker(universal.queueInstance._mutex):
            return universal.queueInstance.currentSongDuration

    @Property(str, notify=songChanged)
    def songFinishesAt(self):
        with QMutexLocker(universal.queueInstance._mutex):
            return universal.queueInstance.songFinishesAt

    @Property(str, notify=songChanged)
    def currentSongId(self):
        with QMutexLocker(universal.queueInstance._mutex):
            return universal.queueInstance.currentSongId

    @Property(QObject, notify=songChanged)
    def currentSong(self) -> universal.song_module.Song:
        f: universal.song_module.Song = universal.song_module.SongProxy(universal.queueInstance.currentSongObject, self)  # type: ignore[assignment, arg-type]
        return f

    @Property(bool, notify=playingStatusChanged)
    def isPlaying(self):
        return universal.queueInstance.isPlaying

    @Property(int, notify=playingStatusChanged)
    def playingStatus(self):
        return int(universal.queueInstance.playingStatus)  # type: ignore[call-overload]

    @Property(str, notify=playingStatusChanged)
    def playingStatusString(self):
        return song_enums.ReadablePlayingStatuses.get(
            universal.queueInstance.playingStatus, "Unknown"
        )

    @Slot(int)
    def seekPercent(self, percentage: int):
        q = universal.queueInstance
        q.pseek(percentage)

    @Slot()
    def next(self):
        q = universal.queueInstance
        q.next()

    @Slot(int)
    def setQueueIndex(self, index: int):
        def _func():
            q = universal.queueInstance
            q.goto(index)

        # universal.bgworker.runnow(_func) # try and fix ui stutter?
        _func()  # probably going to have to make the whole queue run in a separate thread at some point

    @Slot()
    def back(self):
        q = universal.queueInstance
        q.prev()

    @Slot()
    def togglePlayback(self):
        q = universal.queueInstance
        if q.isPlaying or q.playingStatus == song_enums.PlayingStatus.BUFFERING_LOCAL:
            q.pause()
        else:
            q.resume()

    @Slot(str)
    def downloadSong(self, id: str):
        song = universal.song_module.Song(id)
        universal.asyncBgworker.add_job_sync(song.download)

    @Slot(str, result=QObject)
    def getSong(self, id: str):
        song = universal.song_module.SongProxy(universal.song_module.Song(id), self)
        return song

    @Slot(str, result=bool)
    def search(self, query: str) -> bool:
        universal.asyncBgworker.add_job_sync(
            func=universal.search_shorthand, usestar=False, a=[], kw={"query": query}
        )
        return True

    @Slot(str)
    def songPress(self, id: str):
        q = universal.queueInstance
        q.gotoOrAdd(id)

    @Slot(str, result=QObject)
    def getAlbumFromSongID(self, id: str):
        album = universal.album_module.albumFromSongID(id)
        if album is None:
            self.logger.warning(f"Album not found for song ID: {id}")
            return None
        return universal.album_module.AlbumProxy(album, self)

    @Slot(str, result=QObject)
    def getAlbum(self, id: str):
        album = universal.album_module.AlbumProxy(
            universal.album_module.Album(id), self
        )
        return album

    @Slot(str)
    def albumSearchPress(self, id: str):
        album = universal.album_module.Album(id)
        if album is None:
            self.logger.warning(f"Album not found for album ID: {id}")
            return
        universal.appUrl.setUrl(f"clarity:///page/album?id={id}")

    @Slot(QObject)
    def addAlbumToQueue(self, album: universal.album_module.AlbumProxy):
        if album is None:
            self.logger.warning("Album is None, cannot add to queue")
            return
        universal.queue_module.addAlbumToQueue(album.target, goto=True)

    # convenience functions for interacting with the song class
    # all functions will take in an ID
    @Slot(str)
    def getSongDownloadState(self, id: str):
        smodule = universal.song_module
        song = smodule.Song(id)
        return song.downloadState

    @Slot(str)
    def getSongDownloadProgress(self, id: str):
        smodule = universal.song_module
        song = smodule.Song(id)
        return song.downloadProgress
