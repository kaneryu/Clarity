import time
from datetime import datetime, timedelta
import json
import asyncio
import io
import os
import logging
from typing import Union

from PySide6.QtCore import Property as QProperty, Signal, Slot, Qt, QObject, QSize, QBuffer, QRect
from PySide6.QtGui import QPixmap, QPainter, QImage, QImageReader, QImageWriter
from PySide6.QtNetwork import QNetworkRequest
from PySide6.QtQuick import QQuickImageProvider

import ytmusicapi as ytm
import yt_dlp as yt_dlp_module # type: ignore[import-untyped]

from src import universal as universal
from src import cacheManager
from src.misc.enumerations import DataStatus
from src.misc.enumerations.Song import PlayingStatus, DownloadState

ydlOpts: dict[str, Union[list, bool]] = {
    "external_downloader_args": ['-loglevel', 'panic'],
    "quiet": False,
    "concurrent-fragments": True
    
}

ytdl: yt_dlp_module.YoutubeDL
ytdl = yt_dlp_module.YoutubeDL(ydlOpts)

FMT_DATA_HUMAN = {
        "sb0": "Storyboard (low quality)",
        "sb1": "Storyboard (low quality)",
        "sb2": "Storyboard (low quality)",
        "160": "144p (low quality)",
        "133": "240p (low quality)",
        "134": "360p (medium quality)",
        "135": "480p (medium quality)",
        "136": "720p (high quality)",
        "137": "1080p (high quality)",
        "242": "240p (low quality, WebM)",
        "243": "360p (medium quality, WebM)",
        "244": "480p (medium quality, WebM)",
        "247": "720p (high quality, WebM)",
        "248": "1080p (high quality, WebM)",
        "139": "Low quality audio (48.851 kbps)",
        "140": "Medium quality audio (129.562 kbps)",
        "251": "Medium quality audio (135.49 kbps, WebM)",
        "250": "Low quality audio (68.591 kbps, WebM)",
        "249": "Low quality audio (51.975 kbps, WebM)",
        "18": "360p video with audio (medium quality)"
}
FMT_DATA = {
        "sb0": -1,  # Storyboard (low quality)
        "sb1": -1,  # Storyboard (low quality)
        "sb2": -1,  # Storyboard (low quality)
        "160": 1,   # 144p (low quality)
        "133": 2,   # 240p (low quality)
        "134": 4,   # 360p (medium quality)
        "135": 5,   # 480p (medium quality)
        "136": 7,   # 720p (high quality)
        "137": 9,   # 1080p (high quality)
        "242": 2,   # 240p (low quality, WebM)
        "243": 4,   # 360p (medium quality, WebM)
        "244": 5,   # 480p (medium quality, WebM)
        "247": 7,   # 720p (high quality, WebM)
        "248": 9,   # 1080p (high quality, WebM) 
        "139": 1,   # Low quality audio (48.851 kbps)
        "140": 4,   # Medium quality audio (129.562 kbps)
        "251": 5,   # Medium quality audio (135.49 kbps, WebM)
        "250": 3,   # Low quality audio (68.591 kbps, WebM)
        "249": 2,   # Low quality audio (51.975 kbps, WebM)
        "18": 4     # 360p video with audio (medium quality)
}


class DataStoreNotFoundException(Exception):
    """Exception raised when a data store is not found."""
    
    def __init__(self, message: str = "Data store not found. Please ensure the data store is initialized."):
        super().__init__(message)

class CacheNotFoundException(Exception):
    """Exception raised when a cache is not found."""
    def __init__(self, message: str = "Cache not found. Please ensure the cache is initialized."):
        super().__init__(message)

def convert_to_timestamp(date_str: str) -> float:
    # Split the date and the timezone
    date_str, tz_str = date_str.split('T')
    date_str += 'T' + tz_str.split('-')[0]

    # Parse the date string into a datetime object
    dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")

    # Calculate the timezone offset
    tz_hours, tz_minutes = map(int, tz_str.split('-')[1].split(':'))
    tz_delta = timedelta(hours=tz_hours, minutes=tz_minutes)

    # Subtract the timezone offset to get the UTC time
    dt -= tz_delta

    # Convert the datetime object to a timestamp
    timestamp = time.mktime(dt.timetuple())

    return timestamp

def run_sync(func, *args, **kwargs):
    coro = func(*args, **kwargs)
    if asyncio.iscoroutine(coro):
        future = asyncio.run_coroutine_threadsafe(coro, universal.asyncBgworker.event_loop)
        future.result() # wait for the result
    else:
        return coro
    
class Song(QObject):
    
    idChanged = Signal(str)
    sourceChanged = Signal(str)
    dataStatusChanged = Signal(int)
    downloadStateChanged = Signal(int)
    downloadProgressChanged = Signal(int)
    playbackReadyChanged = Signal(bool)
    
    songInfoFetched = Signal()
    
    playingStatusChanged = Signal(int)
    
    _instances: dict[str, "Song"] = {}
    
    def __new__(cls, id: str = "", givenInfo: dict = {"None": None}, fs: bool = False) -> "Song":
        # fs refers to the fakesong override
        if not fs:
            if id in cls._instances:
                return cls._instances[id]
            instance = super(Song, cls).__new__(cls, id, givenInfo) # type: ignore[call-arg]
            cls._instances[id] = instance
            return instance
        else:
            return super(Song, cls).__new__(cls)
    
    def __init__(self, id: str = "", givenInfo: dict = {"None": None}, fs: bool = False):
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
        if hasattr(self, '_initialized'):
            return
        self.logger = logging.getLogger(f"Song.{id}")
        
        super().__init__()
        
        self._id = id
        self._source = None
        self._dataStatus = DataStatus.NOTLOADED

        self._downloadProgress = 0
        self.rawPlaybackInfo: Union[dict, None] = {}
        self.playbackInfo: dict = {}
        self._initialized: bool = True
        self.gettingPlaybackReady = False
        self._downloadState = DownloadState.NOT_DOWNLOADED
        self.downloadStateChanged.connect(lambda: self.checkPlaybackReady())

        self.playbackReadyChanged.connect(lambda: self.logger.debug(f"Playback ready changed for song {self.id} ({self.title}): {self.playbackReady}"))

        self._prev_playbackreadyresult: Union[bool, None] = None
        
        # Schedule cache check and file existence check on background thread
        # This avoids blocking UI during Song creation
        def _lazy_init():
            if cacheManager.getdataStore("song_datastore").checkFileExists(id):
                self._downloadState = DownloadState.DOWNLOADED
                self.downloadStateChanged.emit(self._downloadState)
            self.get_info_cache_only()
        
        universal.bgworker.add_job(_lazy_init)
        # self.moveToThread(g.mainThread)
        
        self.title: str = "Unknown Title"
        self.artist: str = "Unknown Artist"
        self.duration: int = 0
        # 99% of the time, the UI tries to fetch these immediately
        # So we set them to some default values to avoid attribute errors

        return None
    
    
    @QProperty(str, notify = idChanged)
    def id(self) -> str:
        return self._id
    
    @id.setter
    def id(self, value: str) -> None: 
        self._id = value
        self.idChanged.emit(self._id)
    
    @QProperty(str, notify = sourceChanged)
    def source(self) -> str:
        return self._source
    
    @source.setter
    def source(self, value: str) -> None:
        self._source = value
        self.sourceChanged.emit(self._source)
        
    @QProperty(int, notify = dataStatusChanged)
    def dataStatus(self) -> int:
        return self._dataStatus
    
    @dataStatus.setter
    def dataStatus(self, value: Union[int, DataStatus]) -> None:
        self._dataStatus = DataStatus(value) if isinstance(value, int) else value
        self.dataStatusChanged.emit(value if isinstance(value, int) else value.value)
    
    @QProperty(int, notify = downloadStateChanged)
    def downloadState(self) -> int:
        return self._downloadState._value_

    @downloadState.setter
    def downloadState(self, value: int) -> None:
        self._downloadState = DownloadState(value)
        self.downloadStateChanged.emit(self._downloadState._value_)
    
    @QProperty(int, notify = downloadProgressChanged)
    def downloadProgress(self) -> int:
        return self._downloadProgress
    
    @downloadProgress.setter
    def downloadProgress(self, value: int) -> None:
        self._downloadProgress = value
        self.downloadProgressChanged.emit(self._downloadProgress)
    
    @QProperty(bool, notify = playbackReadyChanged)
    def playbackReady(self) -> bool:
        """Returns whether the song is ready for playback or not."""
        return self._downloadState == DownloadState.DOWNLOADED or (self.playbackInfo != {})
    
    def checkPlaybackReady(self, noEmit: bool = False) -> bool:
        """Checks if the song is ready for playback."""
        new_playbackReady = self._downloadState == DownloadState.DOWNLOADED or (self.playbackInfo != {})
        if new_playbackReady != self._prev_playbackreadyresult and not noEmit:
            self._prev_playbackreadyresult = new_playbackReady
            self.playbackReadyChanged.emit(new_playbackReady)
        return new_playbackReady
    
    def from_search_result(self, search_result: dict) -> None:
        self.source = "search"
        self.title = search_result["title"]
        self.id = search_result["videoId"]
    
    async def ensure_info(self) -> None:
        if not self.source:
            await self.get_info(universal.asyncBgworker.API)
    
    def _set_info(self, rawVideoDetails: dict) -> None:
        self.source = "full"
        self.title: str = rawVideoDetails["title"]
        self.id = rawVideoDetails["videoId"]
        self.duration: int = int(rawVideoDetails["lengthSeconds"]) 
        
        self.author: str = rawVideoDetails["author"]
        self.artist: str = rawVideoDetails["author"]
        self.channel: str = rawVideoDetails["author"]
        self.channelId: str = rawVideoDetails["channelId"]
        self.artistId: str = rawVideoDetails["channelId"]
        
        self.thumbails: dict = rawVideoDetails["thumbnail"]["thumbnails"]
        self.smallestThumbail: dict = self.thumbails[0]
        self.largestThumbail: dict = self.thumbails[-1]
        self.smallestThumbailUrl: str = self.smallestThumbail["url"]
        self.largestThumbnailUrl: str = self.largestThumbail["url"]
        
        self.views: int = int(rawVideoDetails["viewCount"])
        
        self.rawMicroformatData = self.rawData["microformat"]
        self.rectangleThumbnail: dict = self.rawMicroformatData["microformatDataRenderer"]["thumbnail"]["thumbnails"][-1]
        self.rectangleThumbnailUrl: str = self.rectangleThumbnail["url"]
        
        self.fullUrl: str = self.rawMicroformatData["microformatDataRenderer"]["urlCanonical"]
        self.description: str = self.rawMicroformatData["microformatDataRenderer"]["description"]

        self.tags: Union[list[str], None] = self.rawMicroformatData["microformatDataRenderer"].get("tags", None)

        self.pageOwnerDetails: dict = self.rawMicroformatData["microformatDataRenderer"]["pageOwnerDetails"]
        self.pageOwnerName: str = self.pageOwnerDetails["name"]
        self.pageOwnerChannelId: str = self.pageOwnerDetails["externalChannelId"]
        
        self.uploadDate: str = self.rawMicroformatData["microformatDataRenderer"]["uploadDate"]
        self.publishDate: str = self.rawMicroformatData["microformatDataRenderer"]["publishDate"]
        
        self.uploadDateTimestamp: float = convert_to_timestamp(self.uploadDate)
        self.publishDateTimestamp: float = convert_to_timestamp(self.publishDate)
        
        self.category: str = self.rawMicroformatData["microformatDataRenderer"]["category"]
        
        self.isFamilySafe: bool = self.rawMicroformatData["microformatDataRenderer"]["familySafe"]
        
                
        self.songInfoFetched.emit()
        self.dataStatus = DataStatus.LOADED
        self.logger = logging.getLogger(f"Song.{self._id}-{self.title}")
        
    def get_info_cache_only(self) -> None:
        self.dataStatus = DataStatus.LOADING
        c = cacheManager.getCache("songs_cache")
        identifier = self.id + "_info"
        cachedData: str
        self.rawData: dict
        
        if cachedData := c.get(identifier): # type: ignore[assignment]
            self.rawData = json.loads(cachedData)
            if self.rawData.get("playabilityStatus", {}).get("status") == "ERROR":
                raise Exception(f"Song cannot be retrieved due to playability issues. id: {self.id} " + self.rawData.get("playabilityStatus", {}).get("reason"))
        else:
            return
        
        self.rawVideoDetails: dict = self.rawData["videoDetails"]
        self._set_info(self.rawVideoDetails)


    async def get_info(self, api: Union[ytm.YTMusic, None] = None, cache_only: bool = False) -> None:
        """
        Gets the info of the song.
        """
        self.dataStatus = DataStatus.LOADING
        api: ytm.YTMusic = api if api else universal.asyncBgworker.API
        c = cacheManager.getCache("songs_cache")

        if not self.id or self.id == "":
            return
        
        identifier = self.id + "_info"
        cachedData: str
        self.rawData: dict
        
        if not (cachedData := c.get(identifier)): # type: ignore[assignment]
            if cache_only:
                return
        
            self.rawData = await api.get_song(self.id)
            c.put(identifier, json.dumps(self.rawData), byte = False)
        else:
            self.rawData = json.loads(cachedData)
            if self.rawData.get("playabilityStatus", {}).get("status") == "ERROR":
                self.logger.warning(f"Song cannot be retrieved due to playability issues. id: {self.id} " + self.rawData.get("playabilityStatus", {}).get("reason"))
                self.dataStatus = DataStatus.NOTLOADED
                return
            if self.rawData.get("playabilityStatus", {}).get("status") == "LOGIN_REQUIRED":
                self.logger.warning(f"Song cannot be retrieved due to login requirements. id: {self.id} " + self.rawData.get("playabilityStatus", {}).get("reason"))
                self.dataStatus = DataStatus.NOTLOADED
                return

        self.rawVideoDetails: dict = self.rawData["videoDetails"]
        self._set_info(self.rawVideoDetails)

    def download_playbackInfo(self) -> None:
        """Because ytdlp isn't async, input this function into the BackgroundWorker to do the slow part in a different thread.
        """
        if not (c := cacheManager.getCache("songs_cache")):
            self.logger.error("No cache found for songs, cannot get playback info.")
            return
        
        identifier = self.id + "_playbackinfo"
        self.rawPlaybackInfo: dict
        cachedData: str
        if universal.networkManager.onlineStatus is not universal.OnlineStatus.ONLINE:
            self.rawPlaybackInfo = None
            return
        
        if not (cachedData := c.get(identifier)): # type: ignore[assignment]
            self.rawPlaybackInfo = ytdl.extract_info(self.id, download=False)
            c.put(identifier, json.dumps(self.rawPlaybackInfo), byte = False, expiration = int(time.time() + 3600)) # 1 hour
        else:
            self.rawPlaybackInfo = json.loads(cachedData)

        if self.rawPlaybackInfo == {}:
            self.rawPlaybackInfo = None
            return

        # open("playbackinfo.json", "w").write(json.dumps(self.rawPlaybackInfo))
        
    def get_playback(self, skip_download: bool = False) -> None:
        self.gettingPlaybackReady = True
        datastore = cacheManager.getdataStore("song_datastore")
        if not datastore:
            self.logger.critical("No data store found for songs, cannot get download info.")
            return
        if self.downloadState == DownloadState.DOWNLOADED and not skip_download:
            try:
                fp = cacheManager.getdataStore("song_datastore").getFilePath(self.id)
                meta: dict = json.loads(cacheManager.getdataStore("song_datastore").get_file(self.id + "_downloadMeta"))
                meta["url"] = fp
                self.playbackInfo = {"audio": [meta], "fromdownload": True}
                return
            except (FileNotFoundError, KeyError, json.JSONDecodeError):
                # Metadata missing or corrupted - fall through to re-download playback info
                self.logger.warning(f"Download metadata missing for {self.id}, will re-fetch playback info")
        
        if not self.rawPlaybackInfo:
            self.download_playbackInfo()
        
        playbackinfo = self.rawPlaybackInfo
        
        if playbackinfo == None:
            self.logger.error("Failed to get playback info, probably due to network reasons.")
            self.playbackInfo = {"audio": None, "video": None}
            return
        
        video = []
        audio = []
        
        format: dict

        for format in playbackinfo["formats"]:
            item = {}

            if format.get("format_note", None) == "storyboard":
                continue
            
            item["format_id"] = format["format_id"]
            item["format_note"] = format.get("format_note", None)
            item["ext"] = format["ext"]
            item["url"] = format["url"]
            item["protocol"] = format["protocol"]
            
            if item["protocol"] == "m3u8_native":
                continue # m3u8 sometimes breaks vlc, also doesn't have some keys set properly, like quality
            
            item["serverQuality"] = format["quality"]
            item["quality"] = FMT_DATA.get(format["format_id"], item["serverQuality"])
            item["qualityName"] = FMT_DATA_HUMAN.get(format["format_id"], item["format_note"])
            
            if format["resolution"] == "audio only":
                item["type"] = "audio"
            else:
                if format["acodec"] == "none":
                    continue # we don't want video without audio
                
                item["type"] = "video"
            
            if item["type"] == "video":
                item["resolution"] = format["resolution"]
                item["fps"] = format["fps"]
                item["vcodec"] = format["vcodec"]
                item["aspect_ratio"] = format["aspect_ratio"]
            
            item["filesize"] = format["filesize"]
            
            if item["type"] == "audio":
                audio.append(item)
            else:
                video.append(item)
    
        audio.sort(key=lambda x: x["quality"])
        video.sort(key=lambda x: x["quality"])
        
        self.playbackInfo = {"audio": audio, "video": video}
        self.checkPlaybackReady()
        self.gettingPlaybackReady = False
    
    def purge_playback(self):
        c = cacheManager.getCache("songs_cache")
        identifier = self.id + "_playbackinfo"
        c.delete(identifier)
        self.rawPlaybackInfo = {}
        
        if self.downloadState == DownloadState.DOWNLOADED:
            cacheManager.getdataStore("song_datastore").delete(self.id)
            cacheManager.getdataStore("song_datastore").delete(self.id + "_downloadMeta")
            self.downloadState = DownloadState.NOT_DOWNLOADED
            
        self.get_playback(skip_download = True)

    # Replace the download_with_progress method
    async def download_with_progress(self, url: str, datastore: cacheManager.dataStore.DataStore, ext: str, id: str) -> None:
        file: io.FileIO = datastore.open_write_file(key=id, ext=ext, bytes=True)
        downloaded = file.tell()  # Get the current file size to determine how many bytes have been written

        self.downloadState = DownloadState.DOWNLOADING
        self.downloadProgress = 0
        
        # Define a progress callback
        def progress_callback(current, total):
            self.downloadProgress = int((current / total) * 100) if total > 0 else 0
            
        self.logger.info(f"Downloading {self.title}", {"notifying": True, "customMessage": f"Downloading {self.title}"})
        try:
            
            # Use the NetworkManager's parallel download functionality
            success = await universal.networkManager.download_file_parallel(
                url=url,
                file_obj=file,
                chunk_size=10 * 1024 * 1024,  # 10 MB chunks
                max_workers=4,
                headers={"Range": f"bytes={downloaded}-"} if downloaded else None,
                progress_callback=progress_callback
            )
            
            if not success:
                self.logger.warning(f"Download failed for {self.title}, retrying with single-threaded download.")
                success = universal.networkManager.download_file(
                    url=url,
                    file_obj=file,
                    progress_callback=progress_callback,
                    start=downloaded
                )
            
            if success:
                self.logger.info(f"Download complete for {self.title}", {"notifying": True, "customMessage": f"Download complete for {self.title}"})
                datastore.close_write_file(key=self.id, ext=ext, file=file)
                self.downloadState = DownloadState.DOWNLOADED
                self.downloadProgress = 100
            else:
                self.logger.error(f"Download failed for {self.title}")
                self.downloadState = DownloadState.NOT_DOWNLOADED
                datastore.close_write_file(key=self.id, ext=ext, file=file)
                
        except Exception as e:
            self.logger.error(f"Download exception for {self.title}: {str(e)}")
            self.downloadState = DownloadState.NOT_DOWNLOADED
            try:
                datastore.close_write_file(key=self.id, ext=ext, file=file)
            except:
                pass
    
    async def download(self, audio = True) -> None:
        """
        Downloads the song.
        """
        self.gettingPlaybackReady = True
        datastore = cacheManager.getdataStore("song_datastore")
        if not self.playbackInfo:
            self.get_playback()
        elif self.playbackInfo.get("fromdownload", False):
            self.purge_playback()
            
        audio = self.playbackInfo["audio"]
        video = self.playbackInfo["video"]
        
        
        audio = audio[-1] if len(audio) > 0 else None
        video = video[-1] if len(video) > 0 else None
    
        if audio:
            url = audio["url"]
            ext = audio["ext"]
            using = audio
        elif video:
            url = video["url"]
            ext = video["ext"]
            using = video
        else:
            self.logger.error(f"No audio or video formats available for download for song {self.id} ({self.title})")
            self.gettingPlaybackReady = False
            return

        q = universal.queueInstance
        if q.currentSongObject == self:
            q.migrate(url)

        if datastore.checkFileExists(self.id):
            datastore.delete(self.id)

        datastore.write_file(key=self.id + "_downloadMeta", value=json.dumps(using), ext="json", byte=False)

        await self.download_with_progress(url, datastore, ext, self.id)
        self.checkPlaybackReady()
        self.gettingPlaybackReady = False
    
    def get_best_playback_MRL(self) -> str | None:
        """Will return either the path of the file on disk or best possbile quality playback URL.

        Returns:
            str: Path or URL
        """
        if self.downloadState == DownloadState.DOWNLOADED:
            # print("Asked for MRL; returning path")
            if result := cacheManager.getdataStore("song_datastore").getFilePath(self.id):
                return result
            else:
                self.logger.error(f"File for song {self.id} not found in datastore, returning empty None.")
                return None
        else:
            if not self.playbackInfo:
                return None
            # print("Asked for MRL; returning URL")
            if not self.playbackInfo.get("audio", None):
                self.logger.error(f"No audio playback info found for song {self.id}, returning None.")
                # g.asyncBgworker.add_job_sync(self.get_playback, skip_download=True) # to be honest, no point in trying to refetch it again if it already didn't get audio
                if not self.playbackInfo.get("video", None):
                    return None
                else:
                    return self.playbackInfo["video"][-1]["url"]
            return self.playbackInfo["audio"][-1]["url"]
        
            
    async def get_lyrics(self, api) -> dict:
        """
        Gets the lyrics of the song.
        """
        api: ytm.YTMusic = api
        self.lyrics = await api.get_lyrics(self.id)
        return self.lyrics

class SongProxy(QObject):
    idChanged = Signal(str)
    sourceChanged = Signal(str)
    dataStatusChanged = Signal(int)
    downloadedChanged = Signal(bool)
    downloadStatusChanged = Signal(int)
    downloadProgressChanged = Signal(int)
    playingStatusChanged = Signal(int)
    
    infoChanged = Signal()
    
    def __init__(self, target: Song, parent: QObject) -> None:
        super().__init__()
        self.target = target
        
        self.target.idChanged.connect(self.idChanged)
        self.target.sourceChanged.connect(self.sourceChanged)
        # self.target.downloadStateChanged.connect(self.downloadStatusChanged)
        self.target.dataStatusChanged.connect(self.dataStatusChanged)
        self.target.downloadProgressChanged.connect(self.downloadProgressChanged)
        self.target.playingStatusChanged.connect(self.playingStatusChanged)
        
        self.target.songInfoFetched.connect(self.infoChanged)
        
        self.target.idChanged.connect(lambda: self.update("id"))
        self.target.sourceChanged.connect(lambda: self.update("source"))
        self.target.downloadStateChanged.connect(lambda: self.update("downloadState"))
        self.target.downloadProgressChanged.connect(lambda: self.update("downloadProgress"))

        self._id = self.target.id
        self._source = self.target.source
        self._downloadState = self.target.downloadState
        self._downloadProgress = self.target.downloadProgress
        self._playbackReady = self.target.playbackReady
        
        self.setParent(parent)
        self.moveToThread(parent.thread())
                    
    def createPropGetter(self, name):
        def getter(self):
            return getattr(self.target, name)
        return getter
    
    def createPropSetter(self, name):
        def setter(value):
            setattr(self.target, name, value)
        return setter
    
    def __getattr__(self, name):
        # Forward any unknown attribute access to target
        return getattr(self.target, name)
    
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
        
    @QProperty(str, notify=idChanged)
    def id(self) -> str:
        return getattr(self, "_id")

    @QProperty(str, notify=sourceChanged)
    def source(self) -> str:
        return getattr(self, "_source")

    @QProperty(int, notify=downloadStatusChanged)
    def downloadStatus(self) -> int:
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
        setattr(self, "_"+name, getattr(self.target, "_"+name))
        exec(f"self.{name}Changed.emit(getattr(self, '_{name}'))")

class SongImageProvider(QQuickImageProvider):
    sendRequest = Signal(QNetworkRequest, str, name = "sendRequest")
    
    def __init__(self):
        super().__init__(QQuickImageProvider.ImageType.Image, QQuickImageProvider.Flag.ForceAsynchronousImageLoading)
        
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
        mask = mask.scaled(maskSize, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    
        
        
        painter = QPainter(mask)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(Qt.GlobalColor.white)
        painter.setPen(Qt.GlobalColor.white)
        painter.drawRoundedRect(QRect(0, 0, maskSize.width(), maskSize.height()), radius, radius, mode = Qt.SizeMode.AbsoluteSize)
        
        painter.end()
        
        mask = mask.scaled(size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        
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
        cacheIdentifier = universal.ghash(f"songimage_{id}_{requestedSize.width()}x{requestedSize.height()}")
        if cachedData := universal.imageCache.get(cacheIdentifier):
            img = QImage()
            img.loadFromData(cachedData)
            return img
        
        def usePlaceholder():
            placeholder = os.path.join(universal.Paths.ASSETSPATH, "placeholders", "generic.png")
            with open(placeholder, 'rb') as file:
                data = file.read()
            img.loadFromData(data)
            
            
        song_id, radius = id.split("/")
        song = Song(song_id)
        if song_id == '' or song_id is None:
            return
        if song.dataStatus == DataStatus.NOTLOADED:
            run_sync(song.get_info)
        if song.dataStatus is DataStatus.LOADING:
            while song.dataStatus is DataStatus.LOADING:
                time.sleep(0.1) # wait a bit for the info to load
        img = QImage()

        if (universal.networkManager.onlineStatus is not universal.OnlineStatus.ONLINE) or (song.dataStatus is not DataStatus.LOADED):
            usePlaceholder()
            skipCache = True
        else:
            try:
                thumbUrl = song.largestThumbnailUrl
            except AttributeError:
                usePlaceholder()
                skipCache = True
            else: # No exception
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
                        universal.imageCache.put(universal.ghash(thumbUrl), request.content, byte=True)

        if requestedSize.width() < 0 or requestedSize.height() < 0:
            requestedSize = QSize(544, 544)

        img = img.scaled(requestedSize, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        mask = self.createRoundingImage(requestedSize, int(radius))
        
        img.setAlphaChannel(mask.toImage())

        if not skipCache:
            buff = QBuffer()
            res = buff.open(QBuffer.OpenModeFlag.ReadWrite)
            result = img.save(buff, "PNG", quality=100) # type: ignore[call-overload]
            buff.seek(0)
            if not result:
                logging.getLogger("SongImageProvider").error(f"Failed to cache image {id} with size {requestedSize.width()}x{requestedSize.height()}")
            else:
                universal.imageCache.put(cacheIdentifier, buff.data(), byte=True)
            buff.close()
        
        return img