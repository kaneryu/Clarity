import time
from datetime import datetime, timedelta
import json
import asyncio
import io
import enum
import os
import logging
from typing import Union, Literal, Any

from PySide6.QtCore import Property as QProperty, Signal, Slot, Qt, QObject, QSize, QBuffer, QRect, QByteArray
from PySide6.QtGui import QPixmap, QPainter, QImage
from PySide6.QtNetwork import QNetworkRequest
from PySide6.QtQuick import QQuickImageProvider

import ytmusicapi as ytm
import yt_dlp as yt_dlp_module # type: ignore[import-untyped]

from src import universal as universal
from src import cacheManager
from src.innertube import song
from src.misc.enumerations.Album import DownloadStatus
from src.misc.enumerations.Song import DownloadState as SongDownloadState
from src.misc.enumerations import DataStatus

from src.innertube.models.songListModel import SongListModel, SongProxyListModel


def run_sync(func, *args, **kwargs):
    coro = func(*args, **kwargs)
    if asyncio.iscoroutine(coro):
        future = asyncio.run_coroutine_threadsafe(coro, universal.asyncBgworker.event_loop)
        future.result() # wait for the result
    else:
        return coro


class Album(QObject):
    _instances: dict[str, "Album"] = {}
    
    downloadStatusChanged = Signal(int)
    dataStatusChanged = Signal(int)



    def __new__(cls, id: str = "", givenInfo: dict = {"None": None}) -> "Album":
        if id in cls._instances:
            return cls._instances[id]
        instance = super(Album, cls).__new__(cls, id, givenInfo) # type: ignore[call-arg]
        cls._instances[id] = instance
        return instance

    def __init__(self, id: str = "", givenInfo: dict = {"None": None}) -> None:
        if hasattr(self, "_initialized") and self._initialized:
            return
        super().__init__()
        self._initialized: bool = True

        self.id = id
        self.rawAlbumDetails = givenInfo if givenInfo != {"None": None} else {}
        self.songs: list[song.Song] = []
        
        self._downloadStatus = DownloadStatus.NONE_DOWNLOADED
        self._dataStatus = DataStatus.NOTLOADED
        
        self.logger = logging.getLogger(f"Album-{self.id}")
        self.cacheManager = cacheManager.getCache("albums_cache")
        
        
    def _set_info(self, rawAlbumDetails: dict) -> None:
        self.rawAlbumDetails = rawAlbumDetails

        assert rawAlbumDetails["type"].lower() == "album" or rawAlbumDetails["type"].lower() == "single" or rawAlbumDetails["type"].lower() == "ep", "The provided ID does not correspond to an album or single or EP."

        self.title: str = rawAlbumDetails["title"]
        self.type: str = rawAlbumDetails["type"].lower()  # "album", "single", or "ep"
        self.description: Union[str, None] = rawAlbumDetails["description"]
        
        self.isExplicit: bool = rawAlbumDetails["isExplicit"]
        self.releaseYear: str = rawAlbumDetails["year"]
        self.trackCount: int = rawAlbumDetails["trackCount"]
        
        self.durationStr: str = rawAlbumDetails["duration"]
        self.duration: int = rawAlbumDetails["duration_seconds"]

        self.albumArtists: list[dict[Literal["name", "id"], str]] = rawAlbumDetails["artists"]
        
        self.audioPlaylistID: str = rawAlbumDetails["audioPlaylistId"]
        
        # self.likeStatus: Union[Literal["LIKE", "DISLIKE", "INDIFFERENT"], None] = rawAlbumDetails.get("likeStatus", None)
        # reserved for the nebulous future Login Update (coming soon™)

        # This is supposed to be a no network call function, so song objects should be created elsewhere
        self.trackList: list[dict] = [track for track in rawAlbumDetails["tracks"] if track.get("videoId") is not None and track.get("isAvailable") == True]
        self.trackIdTitleMap: dict[Literal["id", "title"], str] = {track["videoId"]: track["title"] for track in self.trackList}
        
        self.thumbnails: list[dict[Literal["url", "width", "height"], Union[str, int]]] = rawAlbumDetails["thumbnails"]
        
        self.largestThumbnail: dict[Literal["url", "width", "height"], Union[str, int]] = self.thumbnails[-1]
        self.largestThumbnailUrl: str = self.largestThumbnail["url"]
        
        self.smallestThumbnail: dict[Literal["url", "width", "height"], Union[str, int]] = self.thumbnails[0]
        self.smallestThumbnailUrl: str = self.smallestThumbnail["url"]
        
        self.logger = logging.getLogger(f"Album-{self.id}-{self.title}")
        self.logger.debug(f"Album info set for {self.id} - {self.title}")

    @QProperty(int, notify = dataStatusChanged)
    def dataStatus(self) -> int:
        return self._dataStatus.value
    
    @dataStatus.setter
    def dataStatus(self, value: Union[int, DataStatus]) -> None:
        self._dataStatus = DataStatus(value) if isinstance(value, int) else value
        self.dataStatusChanged.emit(value if isinstance(value, int) else value.value)
        
        
    @QProperty(int, notify=downloadStatusChanged)
    def downloadStatus(self) -> int:
        return self._downloadStatus.value
    
    @downloadStatus.setter
    def downloadStatus(self, value: Union[int, DownloadStatus]) -> None:
        self._downloadStatus = DownloadStatus(value) if isinstance(value, int) else value
        self.downloadStatusChanged.emit(value if isinstance(value, int) else value.value)

    def _set_songs(self) -> Union[list[song.Song], None]:
        if DataStatus(self.dataStatus) is not DataStatus.LOADED:
            self.logger.error("Tried to fetch album's songs, but there is no data available")
            return None

        if len(self.songs) > 0:
            # self.logger.warning("Songs already fetched, refetching anyway.")
            # above is prev behavior, but I see no reason to ever refetch, so just return existing list
            return self.songs
        
        idlist = list(self.trackIdTitleMap.keys())

        tracklist = [song.Song(id) for id in idlist]
        for track in tracklist:
            if not track.dataStatus == DataStatus.LOADED:
                universal.asyncBgworker.add_job_sync(track.get_info)
            track.downloadStateChanged.connect(self.songDownloadStatusChanged)
        self.songs = tracklist
        return self.songs
    
    def get_info_cache_only(self) -> None:
        self.dataStatus = DataStatus.LOADING
        identifier = self.id + "_info"
        cachedData: str
        self.rawData: dict

        if cachedData := self.cacheManager.get(identifier): # type: ignore[assignment]
            self.rawData = json.loads(cachedData)
    
        self.rawAlbumDetails = self.rawData
        self._set_info(self.rawAlbumDetails)
        self._set_songs()
        self.dataStatus = DataStatus.LOADED
    
    async def ensure_info(self) -> None:
        """Ensure that the album info is loaded.
        If the info is already loaded, do nothing.
        Otherwise, fetch the info.
        """
        if self.dataStatus is DataStatus.LOADED:
            return
        await self.get_info(universal.asyncBgworker.API)
    
    async def get_info(self, api, cache_only: bool = False) -> None:
        """
        Gets the info of the album.
        """
        self.dataStatus = DataStatus.LOADING
        
        api: ytm.YTMusic = api

        if not self.id or self.id == "":
            return
        
        identifier = self.id + "_info"
        cachedData: str
        self.rawData: dict
        
        if not (cachedData := self.cacheManager.get(identifier)): # type: ignore[assignment]
            if cache_only:
                return
        
            self.rawData = await api.get_album(self.id)
            self.cacheManager.put(identifier, json.dumps(self.rawData), byte = False)
        else:
            self.rawData = json.loads(cachedData)

        self._set_info(self.rawData)
        self.dataStatus = DataStatus.LOADED
        self._set_songs()


    def songDownloadStatusChanged(self) -> None:
        if len(self.songs) == 0 or DataStatus(self.dataStatus) is not DataStatus.LOADED:
            self.logger.error("Tried to fetch album's songs, but there is no data available")
            return

        downloadStatuses: dict[Literal["id"], SongDownloadState] = {}
        for track in self.songs:
            downloadStatuses[track.id] = track.downloadState

        downloadStatus = DownloadStatus.FULLY_DOWNLOADED
        for status in downloadStatuses.values():
            match status:
                case SongDownloadState.DOWNLOADING:
                    downloadStatus = DownloadStatus.DOWNLOAD_IN_PROGRESS
                    break
                case SongDownloadState.NOT_DOWNLOADED:
                    downloadStatus = DownloadStatus.PARTIALLY_DOWNLOADED
                    break
                case SongDownloadState.DOWNLOADED:
                    continue

        self.downloadStatus = downloadStatus
    
    
    def download(self) -> None:
        if len(self.songs) == 0 or DataStatus(self.dataStatus) is not DataStatus.LOADED:
            self.logger.error("Tried to download album's songs, but there is no data available")
            return

        for track in self.songs:
            universal.asyncBgworker.add_job_sync(track.download)
        self.logger.info("Added all song downloads to queue")
        

async def _afs(songID: str) -> Union[str, None]:
    api = universal.asyncBgworker.API
    albumID = await api.get_song_album_id(songID)
    return albumID
        
def albumFromSong(song: song.Song) -> Union[Album, None]:
    afsCoro = _afs(song.id)
    albumInfo = asyncio.run_coroutine_threadsafe(afsCoro, universal.asyncBgworker.event_loop).result()
    if albumInfo is None:
        return None
    albumInstance = Album(albumInfo)
    if albumInstance.dataStatus is not DataStatus.LOADED:
        universal.asyncBgworker.add_job_sync(albumInstance.get_info, universal.asyncBgworker.API)
    return albumInstance

def albumFromSongID(songID: str) -> Union[Album, None]:
    albumID = asyncio.run_coroutine_threadsafe(_afs(songID), universal.asyncBgworker.event_loop).result()
    albumInstance = Album(albumID) if albumID is not None else None
    if albumInstance is not None and albumInstance.dataStatus is not DataStatus.LOADED:
        universal.asyncBgworker.add_job_sync(albumInstance.get_info, universal.asyncBgworker.API)
    return albumInstance


class AlbumProxy(QObject):
    """
    Lightweight proxy for Album to safely expose properties/signals to QML,
    modeled after SongProxy. Uses a single infoChanged notifier for metadata.
    """
    infoChanged = Signal()
    dataStatusChanged = Signal(int)
    downloadStatusChanged = Signal(int)

    def __init__(self, target: Album, parent: QObject) -> None:
        super().__init__()
        self.target = target

        # Cache simple status values (ints) and forward changes
        self._dataStatus = self.target.dataStatus
        self._downloadStatus = self.target.downloadStatus

        self.target.dataStatusChanged.connect(self._on_data_status_changed)
        self.target.downloadStatusChanged.connect(self._on_download_status_changed)
        
        self.songsModel: Union[SongListModel, None] = None
        self.songsProxyModel: Union[SongProxyListModel, None] = None
            
        # Keep proxy on UI thread
        self.setParent(parent)
        self.moveToThread(parent.thread())

    def __getattr__(self, name):
        # Forward unknown attributes to the target
        return getattr(self.target, name)

    def _on_data_status_changed(self, v: int):
        self._dataStatus = v
        self.dataStatusChanged.emit(v)
        # Album info and songs typically become available with LOADED
        self.infoChanged.emit()

    def _on_download_status_changed(self, v: int):
        self._downloadStatus = v
        self.downloadStatusChanged.emit(v)

    # Metadata properties (notify on infoChanged)
    @QProperty(str, notify=infoChanged)
    def id(self) -> str:
        return getattr(self.target, "id", "")

    @QProperty(str, notify=infoChanged)
    def title(self) -> str:
        return getattr(self.target, "title", "")

    @QProperty(str, notify=infoChanged)
    def albumType(self) -> str:
        return getattr(self.target, "type", "")

    @QProperty(str, notify=infoChanged)
    def artist(self) -> str:
        artists = getattr(self.target, "albumArtists", [])
        if not artists:
            return "Unknown Artist"
        return ", ".join([artist.get("name", "Unknown Artist") for artist in artists])

    @QProperty(str, notify=infoChanged)
    def description(self) -> str:
        return getattr(self.target, "description", "") or ""

    @QProperty(bool, notify=infoChanged)
    def isExplicit(self) -> bool:
        return bool(getattr(self.target, "isExplicit", False))

    @QProperty(str, notify=infoChanged)
    def releaseYear(self) -> str:
        return getattr(self.target, "releaseYear", "")

    @QProperty(int, notify=infoChanged)
    def trackCount(self) -> int:
        return int(getattr(self.target, "trackCount", 0) or 0)

    @QProperty(str, notify=infoChanged)
    def durationStr(self) -> str:
        return getattr(self.target, "durationStr", "")

    @QProperty(int, notify=infoChanged)
    def duration(self) -> int:
        return int(getattr(self.target, "duration", 0) or 0)

    @QProperty(str, notify=infoChanged)
    def largestThumbnailUrl(self) -> str:
        return getattr(self.target, "largestThumbnailUrl", "")

    @QProperty(str, notify=infoChanged)
    def smallestThumbnailUrl(self) -> str:
        return getattr(self.target, "smallestThumbnailUrl", "")

    @QProperty(int, notify=infoChanged)
    def songsCount(self) -> int:
        try:
            return len(getattr(self.target, "songs", []) or [])
        except Exception:
            return 0

    # Status properties (use their dedicated notifiers)
    @QProperty(int, notify=dataStatusChanged)
    def dataStatus(self) -> int:
        return self._dataStatus

    @QProperty(int, notify=downloadStatusChanged)
    def downloadStatus(self) -> int:
        return self._downloadStatus

    @Slot(result=QObject)
    def getSongsModel(self) -> Union[SongListModel, None]:
        if not self.songsModel:
            if DataStatus(self.dataStatus) is not DataStatus.LOADED:
                return None
            model = SongListModel()
            model.setSongList(self.target.songs)
            self.songsModel = model
        return self.songsModel

    @Slot(result=QObject)
    def getSongsProxyModel(self) -> Union[SongProxyListModel, None]:
        if not self.songsProxyModel:
            if DataStatus(self.dataStatus) is not DataStatus.LOADED:
                return None
            model = SongProxyListModel(self)
            model.setSongList(self.target.songs)
            self.songsProxyModel = model
        return self.songsProxyModel
    
    @Slot()
    def download(self) -> None:
        self.target.download()


class AlbumImageProvider(QQuickImageProvider):
    sendRequest = Signal(QNetworkRequest, str, name="sendRequest")

    def __init__(self):
        super().__init__(QQuickImageProvider.ImageType.Image, QQuickImageProvider.Flag.ForceAsynchronousImageLoading)
        self.cached_masks: dict[tuple[QSize, int], QByteArray] = {}
        self.defaultMask = self.createRoundingImage(QSize(544, 544), 20)

    def createRoundingImage(self, size: QSize, radius: int) -> QPixmap:
        if (size, radius) in self.cached_masks:
            pm = QPixmap()
            pm.loadFromData(self.cached_masks[(size, radius)])
            return pm

        maskSize = size * 3
        if size.width() < 0 or size.height() < 0:
            maskSize = QSize(544, 544)
            size = QSize(544, 544)

        pm = QPixmap(maskSize)
        pm.fill(Qt.GlobalColor.black)
        pm = pm.scaled(maskSize, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        painter = QPainter(pm)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(Qt.GlobalColor.white)
        painter.setPen(Qt.GlobalColor.white)
        painter.drawRoundedRect(QRect(0, 0, maskSize.width(), maskSize.height()), radius, radius, mode=Qt.SizeMode.AbsoluteSize)
        painter.end()

        pm = pm.scaled(size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        buff = QBuffer()
        buff.open(QBuffer.OpenModeFlag.ReadWrite)
        pm.save(buff, "PNG", 100)
        buff.seek(0)
        self.cached_masks[(size, radius)] = buff.data()
        buff.close()

        return pm

    def requestImage(self, id, size, requestedSize):
        # ID format: "<albumId>/<radius>"
        try:
            album_id, radius = id.split("/")
        except Exception:
            return QImage()

        if not album_id:
            return QImage()

        alb = Album(album_id)

        run_sync(alb.ensure_info)

        thumbUrl = getattr(alb, "largestThumbnailUrl", "")

        img = QImage()
        data = None

        if universal.networkManager.onlineStatus is not universal.OnlineStatus.ONLINE or not thumbUrl:
            placeholder = os.path.join(universal.Paths.ASSETSPATH, "placeholders", "generic.png")
            with open(placeholder, "rb") as f:
                data = f.read()
            img.loadFromData(data)
        else:
            r = universal.networkManager.get(thumbUrl)
            if not r or r.status_code != 200:
                placeholder = os.path.join(universal.Paths.ASSETSPATH, "placeholders", "generic.png")
                with open(placeholder, "rb") as f:
                    data = f.read()
                img.loadFromData(data)
            else:
                img.loadFromData(r.content)

        if requestedSize.width() < 0 or requestedSize.height() < 0:
            requestedSize = QSize(544, 544)

        img = img.scaled(requestedSize, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        mask = self.createRoundingImage(requestedSize, int(radius))
        img.setAlphaChannel(mask.toImage())

        return img