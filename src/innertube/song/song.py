import dataclasses
import time
from datetime import datetime, timedelta
import json
import asyncio
import io
import os
import logging
from typing import Union
import pathlib

from PySide6.QtCore import (
    Property as QProperty,
    Signal,
    Slot,
    Qt,
    QObject,
    QSize,
    QBuffer,
    QRect,
)
from PySide6.QtGui import QPixmap, QPainter, QImage, QImageReader, QImageWriter
from PySide6.QtNetwork import QNetworkRequest
from PySide6.QtQuick import QQuickImageProvider

import dacite
from src.innertube.song.models.playbackData import FormatData
import ytmusicapi as ytm
import yt_dlp as yt_dlp_module  # type: ignore[import-untyped]

from src import universal as universal
from src import cacheManager
from src.misc.enumerations import DataStatus
from src.misc.enumerations.Song import PlayingStatus, DownloadState

from src.innertube.song.models import (
    SongData,
    PlaybackData,
    songDataDict,
    playbackDataDict,
    rawSongDataDict,
    rawPlaybackDataDict,
)
from src.innertube.song.providers import ProviderInterface, get_provider, list_providers
from src.innertube.globalModels import (
    SimpleIdentifier,
    NamespacedIdentifier,
    NamespacedTypedIdentifier,
)


def run_sync(func, *args, **kwargs):
    coro = func(*args, **kwargs)
    if asyncio.iscoroutine(coro):
        future = asyncio.run_coroutine_threadsafe(
            coro, universal.asyncBgworker.event_loop
        )
        future.result()  # wait for the result
    else:
        return coro


"""
Some notes for the new Provder-based song

From now on, all IDs are split in two.
We have the namespaced ID, which is in the format provider:type:provider_id
(e.g. youtube:song:abcd1234)

And we have provider-specific ID, which is just the ID used by the provider (e.g. abcd1234 for youtube)

The song class will manage getting data from the provider, holding that state. It will also manage caching, and downloading songs.
The only thing the provider needs to do is provide methods to get the data, it holds no state and isn't even instantiated.
"""


class Song(QObject):

    dataStatusChanged = Signal(int)

    downloadStateChanged = Signal(int)
    downloadProgressChanged = Signal(int)
    playbackReadyChanged = Signal(bool)

    songInfoFetched = Signal()

    playingStatusChanged = Signal(int)

    _instances: dict[NamespacedTypedIdentifier, "Song"] = {}
    # Dict now uses NamespacedTypedIdentifier as key

    def __new__(
        cls, ntid: Union[NamespacedIdentifier, NamespacedTypedIdentifier, str]
    ) -> "Song":
        if isinstance(ntid, str):
            try:
                ntid = NamespacedTypedIdentifier.from_string(ntid)
            except ValueError:
                nsid = NamespacedIdentifier.from_string(ntid)
                ntid = NamespacedTypedIdentifier(namespacedIdentifier=nsid, type="song")

        if isinstance(ntid, NamespacedTypedIdentifier):
            if not ntid.type == "song":
                raise ValueError(
                    f"Cannot create Song with non-song NamespacedTypedIdentifier: {ntid}"
                )

        nsid = (
            ntid.namespacedIdentifier
            if isinstance(ntid, NamespacedTypedIdentifier)
            else ntid if isinstance(ntid, NamespacedIdentifier) else None
        )
        if nsid is None:
            raise ValueError(f"Cannot create Song with invalid identifier: {ntid}")

        if nsid in cls._instances:
            return cls._instances[nsid]
        instance = super(Song, cls).__new__(cls, ntid)
        cls._instances[nsid] = instance
        return instance

    def __init__(
        self, ntid: Union[NamespacedIdentifier, NamespacedTypedIdentifier, str]
    ):
        """
        A class that represents a youtube music song.
        To actually get the info of the song, use the get_info_short or get_info_full method after initializing the class, or set auto_get_info to True.

        Parameters:
        id (str): The id of the youtube video.
        autoGetInfo (bool): Whether to automatically get the info of the song or not. Uses the get_info_short method.

        Functions:
        get_info_short: Gets the basic info of the song.
        get_info_full: Gets the full info of the song.
        get_lyrics: Gets the lyrics of the song.
        """
        if hasattr(self, "_initialized"):
            return
        self._initialized: bool = True

        if isinstance(ntid, str):
            self.ntid = NamespacedTypedIdentifier.from_string(ntid)
        elif isinstance(ntid, NamespacedIdentifier):
            self.ntid = NamespacedTypedIdentifier(
                namespacedIdentifier=ntid, type="song"
            )
        elif isinstance(ntid, NamespacedTypedIdentifier):
            self.ntid = ntid
        else:
            raise ValueError(f"Invalid identifier type: {type(ntid)}")

        self.nsid = self.ntid.namespacedIdentifier  # NamespacedIdentifier
        self.sid = self.ntid.namespacedIdentifier.id  # provider-specific IDs
        self.provider = get_provider(self.ntid.namespacedIdentifier.namespace)

        if self.provider is None:
            raise ValueError(
                f"Provider '{self.ntid.namespacedIdentifier.namespace}' not found for song {self.nsid}"
            )

        self.songsCache = self.provider.CACHE
        self.downloadsDatastore = self.provider.DATASTORE
        # Cache identifiers
        self.playbackIdentifier = str(self.sid) + "_playbackinfo"
        self.songInfoIdentifier = str(self.sid) + "_info"
        self.downloadIdentifier = str(self.sid)

        self.logger = logging.getLogger(f"Song.{self.nsid}")

        super().__init__()

        self._id = str(self.nsid)
        self._dataStatus = DataStatus.NOTLOADED

        self._downloadProgress = 0
        self._downloadState = DownloadState.NOT_DOWNLOADED
        self.downloadStateChanged.connect(lambda: self.checkPlaybackReady())

        self.playbackInfo: PlaybackData | None = None
        self.gettingPlaybackReady = False
        self.playbackReadyChanged.connect(
            lambda: self.logger.debug(
                f"Playback ready changed for song {self.nsid} ({self.title}): {self.playbackReady}"
            )
        )
        self._prev_playbackreadyresult: bool | None = None

        # Schedule cache check and file existence check on background thread
        # This avoids blocking UI during Song creation
        def _lazy_init():
            if self.downloadsDatastore.checkFileExists(self.downloadIdentifier):
                self.downloadState = DownloadState.DOWNLOADED._value_
            self.get_info_cache_only()

        universal.bgworker.addJob(_lazy_init)

        self.data = SongData(
            source="placeholder",
            id=self.sid,
            title="Loading...",
            artist="Loading...",
            duration=0,
        )
        # 99% of the time, the UI tries to fetch these immediately
        # So we set them to some default values to avoid attribute errors

    @QProperty(str, constant=True)
    def id(self) -> str:
        return str(self.nsid)

    @QProperty(int, notify=dataStatusChanged)
    def dataStatus(self) -> int:
        return self._dataStatus

    @dataStatus.setter
    def dataStatus(self, value: Union[int, DataStatus]) -> None:
        self._dataStatus = DataStatus(value) if isinstance(value, int) else value
        self.dataStatusChanged.emit(value if isinstance(value, int) else value.value)

    @QProperty(int, notify=downloadStateChanged)
    def downloadState(self) -> int:
        return self._downloadState._value_

    @downloadState.setter
    def downloadState(self, value: int) -> None:
        self._downloadState = DownloadState(value)
        self.downloadStateChanged.emit(self._downloadState._value_)

    @QProperty(int, notify=downloadProgressChanged)
    def downloadProgress(self) -> int:
        return self._downloadProgress

    @downloadProgress.setter
    def downloadProgress(self, value: int) -> None:
        self._downloadProgress = value
        self.downloadProgressChanged.emit(self._downloadProgress)

    @QProperty(bool, notify=playbackReadyChanged)
    def playbackReady(self) -> bool:
        """Returns whether the song is ready for playback or not."""
        return self._downloadState == DownloadState.DOWNLOADED or (
            self.playbackInfo is not None
        )

    def checkPlaybackReady(self, noEmit: bool = False) -> bool:
        """Checks if the song is ready for playback."""
        new_playbackReady = self._downloadState == DownloadState.DOWNLOADED or (
            self.playbackInfo is not None
        )
        if new_playbackReady is not self._prev_playbackreadyresult and not noEmit:
            self._prev_playbackreadyresult = new_playbackReady
            self.playbackReadyChanged.emit(new_playbackReady)
        return new_playbackReady

    def _set_info(
        self, rawData: Union[rawSongDataDict, SongData, songDataDict]
    ) -> None:
        if isinstance(
            rawData, rawSongDataDict
        ):  # we assume this is a raw data dict, straight from the provider
            # though this shouldn't be possible, as the provider really never provides raw data directly
            self.data = self.provider.song_data_from_raw(rawData)
            self.dataStatus = DataStatus.LOADED
            self.songInfoFetched.emit()
        elif isinstance(rawData, SongData):
            self.data = rawData
            self.dataStatus = DataStatus.LOADED
            self.songInfoFetched.emit()
        elif isinstance(rawData, songDataDict):
            # we assume this is a dict that was created from a SongData instance, so it's at least sanitized
            self.data = SongData.from_dict(rawData)
            self.dataStatus = DataStatus.LOADED
            self.songInfoFetched.emit()

    def _set_playback_info(
        self, rawData: Union[rawPlaybackDataDict, PlaybackData, playbackDataDict]
    ) -> None:
        if isinstance(rawData, rawPlaybackDataDict):
            self.playbackInfo = self.provider.playback_from_raw(rawData)
        elif isinstance(rawData, PlaybackData):
            self.playbackInfo = rawData
        elif isinstance(rawData, playbackDataDict):
            self.playbackInfo = PlaybackData.from_dict(rawData)

    async def ensure_info(self) -> None:
        if self.data is None:
            await self.get_info()

    def get_info_cache_only(self) -> None:
        self.dataStatus = DataStatus.LOADING
        identifier = self.songInfoIdentifier
        cachedData: str

        if cachedData := self.songsCache.get(identifier):  # type: ignore[assignment]
            rawData = songDataDict(json.loads(cachedData))
            if rawData.get("playabilityStatus", {}).get("status") == "ERROR":
                raise Exception(
                    f"Song cannot be retrieved due to playability issues. id: {self.id} "
                    + rawData.get("playabilityStatus", {}).get("reason")
                )
        else:
            return

        self._set_info(rawData)

    async def get_info(
        self, api: ytm.YTMusic | None = None, cache_only: bool = False
    ) -> None:
        """
        Gets the info of the song.
        """
        self.dataStatus = DataStatus.LOADING
        cachedData: str

        if not (cachedData := self.songsCache.get(self.songInfoIdentifier)):  # type: ignore[assignment]
            if cache_only:
                return

            rawData = await self.provider.get_info(self.sid)
            if rawData is None:
                self.dataStatus = DataStatus.NOTLOADED
                return
            self.songsCache.put(
                self.songInfoIdentifier, json.dumps(rawData.as_dict()), byte=False
            )
        else:
            rawData = songDataDict(json.loads(cachedData))

            if rawData.get("playabilityStatus", {}).get("status") == "ERROR":
                self.logger.warning(
                    f"Song cannot be retrieved due to playability issues. id: {self.id} "
                    + rawData.get("playabilityStatus", {}).get("reason")
                )
                self.dataStatus = DataStatus.NOTLOADED
                return
            if rawData.get("playabilityStatus", {}).get("status") == "LOGIN_REQUIRED":
                self.logger.warning(
                    f"Song cannot be retrieved due to login requirements. id: {self.id} "
                    + rawData.get("playabilityStatus", {}).get("reason")
                )
                self.dataStatus = DataStatus.NOTLOADED
                return

        self._set_info(rawData)

    def download_playbackInfo(self) -> None:

        self.rawPlaybackInfo: dict
        cachedData: str
        if universal.networkManager.onlineStatus is not universal.OnlineStatus.ONLINE:
            self.playbackInfo = None
            return

        if not (cachedData := self.songsCache.get(self.playbackIdentifier)):  # type: ignore[assignment]
            self.playbackInfo = self.provider.get_playback(self.sid, skip_download=True)
            if self.playbackInfo is None:
                self.playbackInfo = None
                return

            self.songsCache.put(
                self.playbackIdentifier,
                json.dumps(self.playbackInfo.as_dict()),
                byte=False,
                expiration=int(time.time() + 3600),
            )  # 1 hour
        else:
            rawData = playbackDataDict(json.loads(cachedData))
            self.playbackInfo = PlaybackData.from_dict(rawData)

        # open("playbackinfo.json", "w").write(json.dumps(self.rawPlaybackInfo))

    def get_playback(self, skip_download: bool = False) -> None:
        self.gettingPlaybackReady = True

        if self.downloadState == DownloadState.DOWNLOADED and not skip_download:
            try:
                fp = self.downloadsDatastore.getFilePath(self.downloadIdentifier)
                if not fp:
                    raise FileNotFoundError()
                meta = json.loads(
                    self.downloadsDatastore.get_file(
                        self.downloadIdentifier + "_downloadMeta"
                    )
                )
                meta = dacite.from_dict(
                    data_class=FormatData,
                    data=meta,
                )
                meta.url = pathlib.Path(fp).resolve().absolute().as_uri()
                self.playbackInfo = PlaybackData(
                    id=SimpleIdentifier(str(self.nsid)),
                    title=self.data.title,
                    formats=[meta],
                    from_download=True,
                )
                return
            except (FileNotFoundError, KeyError, json.JSONDecodeError):
                # Metadata missing or corrupted - fall through to re-download playback info
                self.logger.warning(
                    f"Download metadata missing for {self.id}, will re-fetch playback info"
                )

        if cachedPlaybackData := self.songsCache.get(self.playbackIdentifier):
            self.playbackInfo = PlaybackData.from_dict(json.loads(cachedPlaybackData))
        else:
            self.playbackInfo = self.provider.get_playback(
                self.sid, skip_download=skip_download
            )

            if self.playbackInfo is None:
                self.logger.error(
                    "Failed to get playback info, probably due to network reasons."
                )
                return
            self.songsCache.put(
                self.playbackIdentifier,
                json.dumps(self.playbackInfo.as_dict()),
                byte=False,
                expiration=int(time.time() + 3600),  # 1 hour
            )

        self.checkPlaybackReady()
        self.gettingPlaybackReady = False

    def purge_playback(self):
        self.songsCache.delete(self.songInfoIdentifier)
        self.rawPlaybackInfo = {}

        if self.downloadState == DownloadState.DOWNLOADED:
            self.downloadsDatastore.delete(self.downloadIdentifier)
            self.downloadsDatastore.delete(self.downloadIdentifier + "_downloadMeta")
            self.downloadState = DownloadState.NOT_DOWNLOADED

        self.get_playback(skip_download=True)

    # Replace the download_with_progress method
    async def download_with_progress(
        self, url: str, datastore: cacheManager.dataStore.DataStore, ext: str
    ) -> None:
        file: io.FileIO = datastore.open_write_file(
            key=self.downloadIdentifier, ext=ext, bytes=True
        )
        downloaded = (
            file.tell()
        )  # Get the current file size to determine how many bytes have been written

        self.downloadState = DownloadState.DOWNLOADING
        self.downloadProgress = 0

        # Define a progress callback
        def progress_callback(current, total):
            self.downloadProgress = int((current / total) * 100) if total > 0 else 0

        self.logger.info(
            f"Downloading {self.data.title}",
            {"notifying": True, "customMessage": f"Downloading {self.data.title}"},
        )
        try:

            # Use the NetworkManager's parallel download functionality
            success = await universal.networkManager.download_file_parallel(
                url=url,
                file_obj=file,
                chunk_size=10 * 1024 * 1024,  # 10 MB chunks
                max_workers=4,
                headers={"Range": f"bytes={downloaded}-"} if downloaded else None,
                progress_callback=progress_callback,
            )

            if not success:
                self.logger.warning(
                    f"Download failed for {self.data.title}, retrying with single-threaded download."
                )
                success = universal.networkManager.download_file(
                    url=url,
                    file_obj=file,
                    progress_callback=progress_callback,
                    start=downloaded,
                )

            if success:
                self.logger.info(
                    f"Download complete for {self.data.title}",
                    {
                        "notifying": True,
                        "customMessage": f"Download complete for {self.data.title}",
                    },
                )
                datastore.close_write_file(
                    key=self.downloadIdentifier, ext=ext, file=file
                )
                self.downloadState = DownloadState.DOWNLOADED
                self.downloadProgress = 100
            else:
                self.logger.error(f"Download failed for {self.data.title}")
                self.downloadState = DownloadState.NOT_DOWNLOADED
                datastore.close_write_file(
                    key=self.downloadIdentifier, ext=ext, file=file
                )

        except Exception as e:
            self.logger.error(f"Download exception for {self.data.title}: {str(e)}")
            self.downloadState = DownloadState.NOT_DOWNLOADED
            try:
                datastore.close_write_file(
                    key=self.downloadIdentifier, ext=ext, file=file
                )
            except Exception as e:
                self.logger.error(f"Error closing file for {self.data.title}: {str(e)}")
                pass

    async def download(self, audio=True) -> None:
        """
        Downloads the song.
        """
        if self.downloadState == DownloadState.DOWNLOADED:
            return  # This behavior will be more complex; ask the user for confirmation or something like that
        # or require a call to delete_download or a similar method first.
        # for now, do nothing.

        self.gettingPlaybackReady = True
        if self.playbackInfo is None:
            self.get_playback()  # fetch playback info if not already present
        elif self.playbackInfo.from_download:
            self.purge_playback()  # if playback info is from previous download, re-fetch it

        if self.playbackInfo is None:
            self.logger.error(
                f"Failed to get playback info, cannot download song {self.downloadIdentifier} ({self.data.title})"
            )
            self.gettingPlaybackReady = False
            return

        audio = (
            self.playbackInfo.audio_formats[0]
            if self.playbackInfo.audio_formats
            else None
        )
        video = (
            self.playbackInfo.video_formats[0]
            if self.playbackInfo.video_formats
            else None
        )

        if audio:
            url = audio.url
            ext = audio.ext
            using = audio
        elif video:
            url = video.url
            ext = video.ext
            using = video
        else:
            self.logger.error(
                f"No audio or video formats available for download for song {self.downloadIdentifier} ({self.data.title})"
            )
            self.gettingPlaybackReady = False
            return

        # q = universal.queueInstance
        # if q.currentSongObject == self:
        #     q.migrate(url)

        if self.downloadsDatastore.checkFileExists(self.downloadIdentifier):
            self.downloadsDatastore.delete(self.downloadIdentifier)
            self.downloadsDatastore.delete(self.downloadIdentifier + "_downloadMeta")

        self.downloadsDatastore.write_file(
            key=self.downloadIdentifier + "_downloadMeta",
            value=json.dumps(dataclasses.asdict(using)),
            ext="json",
            byte=False,
        )

        await self.download_with_progress(url, self.downloadsDatastore, ext)
        self.checkPlaybackReady()
        self.gettingPlaybackReady = False

    def get_best_playback_mrl(self) -> str | None:
        """Will return either the path of the file on disk or best possbile quality playback URL.

        Returns:
            str: Path or URL
        """
        if self.downloadState == DownloadState.DOWNLOADED:
            if result := self.downloadsDatastore.getFilePath(self.downloadIdentifier):
                return result
            else:
                self.logger.error(
                    f"File for song {self.downloadIdentifier} not found in datastore, returning empty None."
                )
                return None
        else:
            if self.playbackInfo is None:
                return None
            if not self.playbackInfo.audio_formats:
                # g.asyncBgworker.add_job_sync(self.get_playback, skip_download=True) # to be honest, no point in trying to refetch it again if it already didn't get audio
                if not self.playbackInfo.video_formats:
                    return None
                else:
                    return self.playbackInfo.video_formats[0].url
            return self.playbackInfo.audio_formats[0].url

    def __getattribute__(self, name):

        if name in SongData(SimpleIdentifier("null")).as_dict().keys():
            # logger = super().__getattribute__("logger")
            # logger.warning(
            #     f"Accessing Song.{name} directly is deprecated, use Song.data.{name} instead."
            # )
            return getattr(super().__getattribute__("data"), name)
        else:
            return super().__getattribute__(name)

    async def get_lyrics(self, api) -> dict:
        """
        Gets the lyrics of the song.
        """
        api: ytm.YTMusic = api
        self.lyrics = await api.get_lyrics(self.id)
        return self.lyrics


class SongProxy(QObject):
    dataStatusChanged = Signal(int)
    downloadedChanged = Signal(bool)
    downloadStateChanged = Signal(int)
    downloadProgressChanged = Signal(int)
    playingStatusChanged = Signal(int)

    infoChanged = Signal()

    def __init__(self, target: Song, parent: QObject) -> None:
        super().__init__()
        self.target = target

        self.target.downloadStateChanged.connect(self.downloadStateChanged)
        self.target.dataStatusChanged.connect(self.dataStatusChanged)
        self.target.downloadProgressChanged.connect(self.downloadProgressChanged)
        self.target.playingStatusChanged.connect(self.playingStatusChanged)

        self.target.songInfoFetched.connect(self.infoChanged)
        self.target.downloadStateChanged.connect(lambda: self.update("downloadState"))
        self.target.downloadProgressChanged.connect(
            lambda: self.update("downloadProgress")
        )

        self._id = self.target.nsid.__str__()

        self._downloadState = self.target.downloadState
        self._downloadProgress = self.target.downloadProgress
        self._playbackReady = self.target.playbackReady

        self.setParent(parent)
        self.moveToThread(parent.thread())

    def __getattr__(self, name):
        # Forward any unknown attribute access to target
        return getattr(self.target, name)

    @QProperty(str, constant=True)
    def id(self) -> str:
        return self._id

    @QProperty(str, notify=infoChanged)
    def title(self) -> str:
        return getattr(self.target, "title")

    @QProperty(str, notify=infoChanged)
    def artist(self) -> str:
        return getattr(self.target, "artist")

    @QProperty(str, notify=infoChanged)
    def description(self) -> str:
        return getattr(self.target, "description")

    @QProperty(int, notify=infoChanged)
    def duration(self) -> int:
        return getattr(self.target, "duration")

    @QProperty(str, notify=infoChanged)
    def uploadDate(self) -> str:
        return getattr(self.target, "uploadDate")

    @QProperty(str, notify=infoChanged)
    def views(self) -> str:
        return getattr(self.target, "views")

    @QProperty(int, notify=downloadStateChanged)
    def downloadState(self) -> int:
        return getattr(self, "_downloadState")

    @QProperty(int, notify=downloadProgressChanged)
    def downloadProgress(self) -> int:
        return getattr(self, "_downloadProgress")

    @QProperty(int, notify=playingStatusChanged)
    def playingStatus(self) -> int:
        q = universal.queueInstance
        if q.currentSongId == self.id:
            return q.playingStatus  # type: ignore[return-value]
        else:
            return PlayingStatus.NOT_PLAYING

    @QProperty(int, notify=dataStatusChanged)
    def dataStatus(self) -> int:
        return getattr(self.target, "_dataStatus").value

    @QProperty(bool, notify=infoChanged)
    def playbackReady(self) -> bool:
        return getattr(self, "_playbackReady")

    @Slot()
    def test(self):
        print("test")

    def update(self, name):
        setattr(self, "_" + name, getattr(self.target, "_" + name))
        exec(f"self.{name}Changed.emit(getattr(self, '_{name}'))")


class SongImageProvider(QQuickImageProvider):
    sendRequest = Signal(QNetworkRequest, str, name="sendRequest")

    def __init__(self):
        super().__init__(
            QQuickImageProvider.ImageType.Image,
            QQuickImageProvider.Flag.ForceAsynchronousImageLoading,
        )

        self.cached_masks = {}
        self.defaultMask = self.createRoundingImage(QSize(544, 544), 20)
        # self.sendRequest.connect(network.accessManager.get, type = Qt.ConnectionType.BlockingQueuedConnection)

    def createRoundingImage(self, size: QSize, radius: int) -> QPixmap:
        # create a mask 3x the size of the image
        # draw the rounded rect on the mask
        # anti-alias the mask down to the size of the image
        # return the mask

        if (size, radius) in self.cached_masks:
            r = QPixmap()
            r.loadFromData(self.cached_masks[(size, radius)])
            return r

        maskSize = size * 3
        if size.width() < 0 or size.height() < 0:
            maskSize = QSize(544, 544)
            size = QSize(544, 544)

        mask = QPixmap(maskSize)
        mask.fill(Qt.GlobalColor.black)
        mask = mask.scaled(
            maskSize,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        painter = QPainter(mask)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(Qt.GlobalColor.white)
        painter.setPen(Qt.GlobalColor.white)
        painter.drawRoundedRect(
            QRect(0, 0, maskSize.width(), maskSize.height()),
            radius,
            radius,
            mode=Qt.SizeMode.AbsoluteSize,
        )

        painter.end()

        mask = mask.scaled(
            size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        buff = QBuffer()
        buff.open(QBuffer.OpenModeFlag.ReadWrite)
        mask.save(buff, "PNG", 100)
        buff.seek(0)
        self.cached_masks[(size, radius)] = buff.data()
        buff.close()

        return mask

    def requestImage(self, id, size, requestedSize):
        # should be in a diff. thread, if i read the docs right
        # ID will be in the format songID/radius

        skipCache = False
        cacheIdentifier = universal.ghash(
            f"songimage_{id}_{requestedSize.width()}x{requestedSize.height()}"
        )
        if cachedData := universal.imageCache.get(cacheIdentifier):
            img = QImage()
            img.loadFromData(cachedData)
            return img

        def usePlaceholder():
            placeholder = os.path.join(
                universal.Paths.ASSETSPATH, "placeholders", "generic.png"
            )
            with open(placeholder, "rb") as file:
                data = file.read()
            img.loadFromData(data)

        song_id, radius = id.split("/")
        if song_id == "" or song_id is None or song_id == "undefined":
            return
        song = Song(song_id)
        if song.dataStatus == DataStatus.NOTLOADED:
            run_sync(song.get_info)
        if song.dataStatus is DataStatus.LOADING:
            while song.dataStatus is DataStatus.LOADING:
                time.sleep(0.1)  # wait a bit for the info to load
        img = QImage()

        if (
            universal.networkManager.onlineStatus is not universal.OnlineStatus.ONLINE
        ) or (song.dataStatus is not DataStatus.LOADED):
            usePlaceholder()
            skipCache = True
        else:
            try:
                thumbUrl = song.data.largestThumbnailUrl
                if thumbUrl is None:
                    raise TypeError
            except (AttributeError, TypeError):
                usePlaceholder()
                skipCache = True
            else:  # No exception
                if cachedData := universal.imageCache.get(universal.ghash(thumbUrl)):
                    img.loadFromData(cachedData)
                else:
                    request = universal.networkManager.get(thumbUrl)
                    if not request:
                        usePlaceholder()
                        skipCache = True
                    else:
                        img = QImage()
                        if request.status_code != 200:
                            return img

                        img.loadFromData(request.content)
                        universal.imageCache.put(
                            universal.ghash(thumbUrl), request.content, byte=True
                        )

        if requestedSize.width() < 0 or requestedSize.height() < 0:
            requestedSize = QSize(544, 544)

        img = img.scaled(
            requestedSize,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        mask = self.createRoundingImage(requestedSize, int(radius))

        img.setAlphaChannel(mask.toImage())

        if not skipCache:
            buff = QBuffer()
            result = img.save(buff, "PNG", quality=100)  # type: ignore[call-overload]
            buff.seek(0)
            if not result:
                logging.getLogger("SongImageProvider").error(
                    f"Failed to cache image {id} with size {requestedSize.width()}x{requestedSize.height()}"
                )
            else:
                universal.imageCache.put(cacheIdentifier, buff.data(), byte=True)
            buff.close()

        return img
