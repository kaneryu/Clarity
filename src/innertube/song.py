import time
from datetime import datetime, timedelta
import json
import asyncio
import io
import enum
import requests
from concurrent.futures import ThreadPoolExecutor
import os
import builtins

from PySide6.QtCore import Property as QProperty
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtNetwork import *
from PySide6.QtQuick import QQuickImageProvider

import ytmusicapi as ytm
import yt_dlp as yt_dlp_module
import httpx
import vlc

from src import universal as g
from src import cacheManager
from src import network
# import src.innertube.song as song

ydlOpts = {
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
        future = asyncio.run_coroutine_threadsafe(coro, g.asyncBgworker.event_loop)
        future.result() # wait for the result
    else:
        return coro

class DownloadStatus(enum.Enum):
    NOT_DOWNLOADED = 0
    DOWNLOADING = 1
    DOWNLOADED = 2

class PlayingStatus(enum.IntEnum):
    """Playing Status"""
    PLAYING = 0 # Playing
    PAUSED = 1 # Paused
    BUFFERING = 2 # Media is buffering
    STOPPED = 3 # No media is loaded
    ERROR = 4 # Unrecoverable error
    
    NOT_PLAYING = 5 # Only for songproxy class; Returned when the current song is not currently playing

class Song(QObject):
    
    idChanged = Signal(str)
    sourceChanged = Signal(str)
    downloadedChanged = Signal(bool)
    downloadStatusChanged = Signal(enum.Enum)
    downloadProgressChanged = Signal(int)
    
    songInfoFetched = Signal()
    
    _instances = {}
    
    def __new__(cls, id: str = "", givenInfo: dict = {"None": None}, fs: bool = False) -> "Song":
        # fs refers to the fakesong override
        if not fs:
            if id in cls._instances:
                return cls._instances[id]
            instance = super(Song, cls).__new__(cls, id, givenInfo)
            cls._instances[id] = instance
            return instance
        else:
            return super(Song, cls).__new__(cls)
    
    def __init__(self, id: str = "", givenInfo: dict = {"None": None}, fs: bool = False) -> "Song":
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
        self._downloaded = cacheManager.getdataStore("song_datastore").checkFileExists(id)
        if self._downloaded:
            self._dowloadStatus = DownloadStatus.DOWNLOADED
        else:
            self._dowloadStatus = DownloadStatus.NOT_DOWNLOADED
            
        if hasattr(self, '_initialized'):
            return
        
        super().__init__()
        
        self._id = id
        self._source = None

        self._downloadProgress = 0
        self.rawPlaybackInfo = None
        self.playbackInfo = None
        self._initialized = True
        
        # self.moveToThread(g.mainThread)
        self._cover = g.associateCover(self)
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
    
    @QProperty(bool, notify = downloadedChanged)
    def downloaded(self) -> bool:
        return cacheManager.getdataStore("song_datastore").checkFileExists(self.id)

    @downloaded.setter
    def downloaded(self, value: bool) -> None:
        self._downloaded = value
        self.downloadedChanged.emit(self._downloaded)
    
    @QProperty(enum.Enum, notify = downloadStatusChanged)
    def downloadStatus(self) -> enum.Enum:
        return self._dowloadStatus

    @downloadStatus.setter
    def downloadStatus(self, value: enum.Enum) -> None:
        self._dowloadStatus = value
        self.downloadStatusChanged.emit(self._dowloadStatus)
    
    @QProperty(int, notify = downloadProgressChanged)
    def downloadProgress(self) -> int:
        return self._downloadProgress
    
    @downloadProgress.setter
    def downloadProgress(self, value: int) -> None:
        self._downloadProgress = value
        self.downloadProgressChanged.emit(self._downloadProgress)
        
    @QProperty(str, constant=True)
    def cover(self) -> object:
        return self._cover

    
    def from_search_result(self, search_result: dict) -> None:
        self.source = "search"
        
        self.title = search_result["title"]
        self.id = search_result["videoId"]
    
    async def ensure_info(self) -> None:
        if not self.source:
            await self.get_info(g.asyncBgworker.API)
        
    async def get_info(self, api) -> None:
        """
        Gets the info of the song.
        """
        api: ytm.YTMusic = api
        c = cacheManager.getCache("songs_cache")
        if not self.id or self.id == "":
            return
        identifier = self.id + "_info"
        self.rawdata = c.get(identifier)
        if not self.rawdata:
            self.rawData: dict = await api.get_song(self.id)
            c.put(identifier, json.dumps(self.rawData), byte = False)
        else:
            self.rawData = json.loads(self.rawdata)
            

        self.source = "full"
        
        self.rawVideoDetails: dict = self.rawData["videoDetails"]
        
        self.title: str = self.rawVideoDetails["title"]
        self.id = self.rawVideoDetails["videoId"]
        self.duration: int = int(self.rawVideoDetails["lengthSeconds"]) 
        
        self.author: str = self.rawVideoDetails["author"]
        self.artist: str = self.rawVideoDetails["author"]
        self.channel: str = self.rawVideoDetails["author"]
        self.channelId: str = self.rawVideoDetails["channelId"]
        self.artistId: str = self.rawVideoDetails["channelId"]
        
        self.thumbails: dict = self.rawVideoDetails["thumbnail"]["thumbnails"]
        self.smallestThumbail: dict = self.thumbails[0]
        self.largestThumbail: dict = self.thumbails[-1]
        self.smallestThumbailUrl: str = self.smallestThumbail["url"]
        self.largestThumbnailUrl: str = self.largestThumbail["url"]
        
        self.views: int = int(self.rawVideoDetails["viewCount"])
        
        self.rawMicroformatData = self.rawData["microformat"]
        self.rectangleThumbnail: dict = self.rawMicroformatData["microformatDataRenderer"]["thumbnail"]["thumbnails"][-1]
        self.rectangleThumbnailUrl: str = self.rectangleThumbnail["url"]
        
        self.fullUrl: str = self.rawMicroformatData["microformatDataRenderer"]["urlCanonical"]
        self.description: str = self.rawMicroformatData["microformatDataRenderer"]["description"]
    
        self.tags: list = self.rawMicroformatData["microformatDataRenderer"]["tags"]
        
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

    def download_playbackInfo(self) -> None:
        """Because ytdlp isn't async, input this function into the BackgroundWorker to do the slow part in a different thread.
        """
        c = cacheManager.getCache("songs_cache")
        identifier = self.id + "_playbackinfo"
        self.rawPlaybackInfo = c.get(identifier)
        if not self.rawPlaybackInfo: # if not cached
            self.rawPlaybackInfo = ytdl.extract_info(self.id, download=False)
            c.put(identifier, json.dumps(self.rawPlaybackInfo), byte = False, expiration = time.time() + 3600) # 1 hour
        else:
            self.rawPlaybackInfo = json.loads(self.rawPlaybackInfo)
        
        
        # open("playbackinfo.json", "w").write(json.dumps(self.rawPlaybackInfo))
        
    def get_playback(self, skip_download = False) -> None:
        
        if self.downloaded and not skip_download:
            try:
                fp = cacheManager.getdataStore("song_datastore").getFilePath(self.id)
                meta = json.loads(cacheManager.getdataStore("song_datastore").get_file(self.id + "_downloadMeta"))
                meta["url"] = fp
                self.playbackInfo = {"audio": [meta], "fromdownload": True}
                return
            except Exception:
                # temporary fix since some files were downloaded before the meta was saved
                pass
        
        if not self.rawPlaybackInfo:
            self.download_playbackInfo()
        
        playbackinfo = self.rawPlaybackInfo
        
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
    
    def purge_playback(self):
        c = cacheManager.getCache("songs_cache")
        identifier = self.id + "_playbackinfo"
        c.delete(identifier)
        self.rawPlaybackInfo = None
        
        if self.downloaded:
            cacheManager.getdataStore("song_datastore").delete(self.id)
            cacheManager.getdataStore("song_datastore").delete(self.id + "_downloadMeta")
            self.downloaded = False
            self.downloadStatus = DownloadStatus.NOT_DOWNLOADED
            
        self.get_playback(skip_download = True)
    
        
    def download_chunk(self, url, headers, file, start, end):
        mhash = cacheManager.ghash(str(start + end))
        self.downloadProgresses[mhash] = 0
        
        headers["Range"] = f"bytes={start}-{end}"
        with requests.get(url, headers=headers, stream=True) as response:
            for chunk in response.iter_content(chunk_size=8192):
                file.seek(start)
                file.write(chunk)
                start += len(chunk)
                self.downloadProgresses[mhash] = start
                    
    async def download_with_progress(self, url: str, datastore: cacheManager.dataStore.DataStore, ext: str, id: str) -> None:
        file: io.FileIO = datastore.open_write_file(key=id, ext=ext, bytes=True)
        downloaded = file.tell()  # Get the current file size to determine how many bytes have been written

        headers = {"Range": f"bytes={downloaded}-"} if downloaded else {}
        self.downloadProgresses = {}
        async with httpx.AsyncClient() as client:
            print("Downloading", self.title)
            
            response = await client.head(url, headers=headers)
            total = int(response.headers.get("Content-Length", 0)) + downloaded

            chunk_size = 10 * 1024 * 1024  # 10 MB
            ranges = [(i, min(i + chunk_size - 1, total - 1)) for i in range(downloaded, total, chunk_size)]

            with ThreadPoolExecutor(max_workers=4) as executor:
                loop = asyncio.get_event_loop()
                tasks = [
                    loop.run_in_executor(executor, self.download_chunk, url, headers, file, start, end)
                    for start, end in ranges
                ]
                
                future = asyncio.ensure_future(asyncio.gather(*tasks))
                while not future.done():
                    await asyncio.sleep(0.1)
                    self.downloadProgress = sum(self.downloadProgresses.values()) / total * 100

            print("Download complete")
            datastore.close_write_file(key=self.id, ext=ext, file=file)
            self.downloadStatus = DownloadStatus.DOWNLOADED
            self.downloadProgress = 100
            self.downloaded = True
            
    async def download(self, audio = True) -> None:
        """
        Downloads the song.
        """
        datastore = cacheManager.getdataStore("song_datastore")
        if not self.playbackInfo:
            self.get_playback()
        elif self.playbackInfo.get("fromdownload", False):
            self.purge_playback()
            
        audio = self.playbackInfo["audio"]
        video = self.playbackInfo["video"]
        
        audio = audio[-1]
        video = video[-1]
    
        if audio:
            url = audio["url"]
            ext = audio["ext"]
            using = audio
        else:
            url = video["url"]
            ext = video["ext"]
            using = video
            
        q: Queue = Queue()
        if q.currentSongObject == self:
            q.migrate(url)
            
        if datastore.checkFileExists(self.id):
            datastore.delete(self.id)

        datastore.write_file(key=self.id + "_downloadMeta", value=json.dumps(using), ext="json", byte=False)
        await self.download_with_progress(url, datastore, ext, self.id)
    
    
    def get_best_playback_MRL(self) -> str:
        """Will return either the path of the file on disk or best possbile quality playback URL.

        Returns:
            str: Path or URL
        """
        if self.downloaded or self.downloadStatus == DownloadStatus.DOWNLOADED:
            # print("Asked for MRL; returning path")
            return cacheManager.getdataStore("song_datastore").getFilePath(self.id)
        else:
            if not self.playbackInfo:
                return None
            # print("Asked for MRL; returning URL")
            return self.playbackInfo["audio"][-1]["url"]
        
            
    async def get_lyrics(self, api) -> dict:
        """
        Gets the lyrics of the song.
        """
        api: ytm.YTMusic = api
        self.lyrics = await self.api.get_lyrics(self.id)
        return self.lyrics

class SongProxy(QObject):
    idChanged = Signal(str)
    sourceChanged = Signal(str)
    downloadedChanged = Signal(bool)
    downloadStatusChanged = Signal(enum.Enum)
    downloadProgressChanged = Signal(int)
    playingStatusChanged = Signal(int)
    
    infoChanged = Signal()
    
    def __init__(self, target: Song, parent: QObject) -> None:
        super().__init__()
        self.target = target
        
        self.target.idChanged.connect(self.idChanged)
        self.target.sourceChanged.connect(self.sourceChanged)
        self.target.downloadedChanged.connect(self.downloadedChanged)
        self.target.downloadStatusChanged.connect(self.downloadStatusChanged)
        self.target.downloadProgressChanged.connect(self.downloadProgressChanged)
        
        self.target.songInfoFetched.connect(self.infoChanged)
        
        self.target.idChanged.connect(lambda: self.update("id"))
        self.target.sourceChanged.connect(lambda: self.update("source"))
        self.target.downloadedChanged.connect(lambda: self.update("downloaded"))
        self.target.downloadStatusChanged.connect(lambda: self.update("downloadStatus"))
        self.target.downloadProgressChanged.connect(lambda: self.update("downloadProgress"))
        
        self._id = self.target.id
        self._source = self.target.source
        self._downloaded = self.target.downloaded
        self._downloadStatus = self.target.downloadStatus
        self._downloadProgress = self.target.downloadProgress
        
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

    @QProperty(bool, notify=downloadedChanged)
    def downloaded(self) -> bool:
        return getattr(self, "_downloaded")

    @QProperty(enum.Enum, notify=downloadStatusChanged)
    def downloadStatus(self) -> enum.Enum:
        return getattr(self, "_downloadStatus")

    @QProperty(int, notify=downloadProgressChanged)
    def downloadProgress(self) -> int:
        return getattr(self, "_downloadProgress")
    
    @QProperty(int, notify=playingStatusChanged)
    def playingStatus(self) -> int:
        q = Queue()
        if q.currentSongId == self.id:
            return q.playingStatus
        else:
            return PlayingStatus.NOT_PLAYING
    
    @Slot()
    def test(self):
        print("test")
    
    def update(self, name):
        setattr(self, "_"+name, getattr(self.target, name))
        exec("self."+name+"Changed.emit(getattr(self, '_"+name+"'))")


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
        
        
        song_id, radius = id.split("/")
        song = Song(song_id)
        if song_id == '' or song_id is None:
            return
        run_sync(song.ensure_info)
        thumbUrl = song.largestThumbnailUrl
        # request = QNetworkRequest(thumbUrl)
        
        # self.sendRequest.emit(request, str(builtins.id(request)))
        # reply: QNetworkReply = network.accessManager.getReply(str(builtins.id(request)))
        # reply.waitForReadyRead(10000)
        request = requests.get(thumbUrl)
        
        img = QImage()
        if request.status_code != 200:
            return img
        
        img.loadFromData(request.content)

        if requestedSize.width() < 0 or requestedSize.height() < 0:
            requestedSize = QSize(544, 544)

        img = img.scaled(requestedSize, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        mask = self.createRoundingImage(requestedSize, int(radius))
        
        img.setAlphaChannel(mask.toImage())
        
        return img
        
        


class LoopType(enum.Enum):
    """Loop Types"""
    NONE = 0 # Halt after playing all songs
    SINGLE = 1 # Repeat the current song
    ALL = 2 # Repeat all songs in the queue

class QueueModel(QAbstractListModel):
    def __init__(self):
        super().__init__()
        self._queueIds = []
        self._queue: list[Song] = []

    def rowCount(self, parent=QModelIndex()):
        return len(self._queue)

    def count(self):
        return len(self._queue)
    
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and index.isValid():
            return self._queue[index.row()].title
        if role == Qt.ItemDataRole.EditRole and index.isValid():
            return self._queue[index.row()]
        if role == Qt.ItemDataRole.UserRole + 1 and index.isValid():
            return self._queue[index.row()].artist
        if role == Qt.ItemDataRole.UserRole + 2 and index.isValid():
            return self._queue[index.row()].duration
        if role == Qt.ItemDataRole.UserRole + 3 and index.isValid():
            return "placeholder"
        if role == Qt.ItemDataRole.UserRole + 4 and index.isValid():
            return self._queue[index.row()].id
        if role == Qt.ItemDataRole.UserRole + 5 and index.isValid():
            return index.row()
        return None

    def roleNames(self):
        return {
            Qt.ItemDataRole.DisplayRole: b"title",
            Qt.ItemDataRole.UserRole + 1: b"artist",
            Qt.ItemDataRole.UserRole + 2: b"length",
            Qt.ItemDataRole.UserRole + 3: b"thumbnail",
            Qt.ItemDataRole.UserRole + 4: b"id",
            Qt.ItemDataRole.UserRole + 5: b"index",
            Qt.ItemDataRole.EditRole: b"qobject",    
        }
    
    def headerData(self, section, orientation, role = ...):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return "Song"
            else:
                return f"Song {section}"
        return None
    
    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole and index.isValid():
            self._queue[index.row()] = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def setQueue(self, queue):
        self.beginResetModel()
        self._queue = queue
        self.endResetModel()

    def removeItem(self, index):
        if 0 <= index < len(self._queue):
            self.beginRemoveRows(QModelIndex(), index, index)
            del self._queue[index]
            self.endRemoveRows()

    def moveItem(self, from_index, to_index):
        if 0 <= from_index < len(self._queue) and 0 <= to_index < len(self._queue):
            self.beginMoveRows(QModelIndex(), from_index, from_index, QModelIndex(), to_index)
            self._queue.insert(to_index, self._queue.pop(from_index))
            self.endMoveRows()
    
    def insertRows(self, row, count):
        self.beginInsertRows(QModelIndex(), row, row + count - 1)
        self._queue.insert(row, [[] for _ in range(count)])
        self.endInsertRows()
            
class Queue(QObject):
    """Combined Queue and Player"""

    queueChanged = Signal()
    songChanged = Signal()
    pointerMoved = Signal()
    playingStatusChanged = Signal(int)
    durationChanged = Signal()
    
    instance = None
    
    def __new__(cls, *args, **kwargs) -> "Queue":
        if cls.instance is None:
            cls.instance = super(Queue, cls).__new__(cls, *args, **kwargs)
        return cls.instance
        
    def __init__(self):
        if hasattr(self, 'initialized'):
            return
        super().__init__()
        self.initialized = True

        self._pointer = 0
        
        vlc_args = ["h254-fps=15", "network-caching", "file-caching", "verbose=1", "vv", "log-verbose=3"]
        

        self.instance: vlc.Instance = vlc.Instance(vlc_args)

        self.player: vlc.MediaPlayer = self.instance.media_player_new()
        
        self.eventManager: vlc.EventManager = self.player.event_manager()
        
        self._mutex = QMutex()
        self._queueAccessMutex = QMutex()
        
        self.player.set_hwnd(0)
        self.loop: LoopType = LoopType.NONE
        self.queueModel = QueueModel()
        
        if not cacheManager.cacheExists("queueCache"):
            cache = cacheManager.CacheManager(name="queueCache")
        else:
            cache = cacheManager.getCache("queueCache")
        
        self.eventManager.event_attach(vlc.EventType.MediaPlayerEndReached, self.songFinished)
        self.eventManager.event_attach(vlc.EventType.MediaPlayerEncounteredError, self.on_vlc_error)
        
        self.eventManager.event_attach(vlc.EventType.MediaPlayerPaused, self.onPauseEvent)
        self.eventManager.event_attach(vlc.EventType.MediaPlayerPlaying, self.onPlayEvent)
        self.eventManager.event_attach(vlc.EventType.MediaPlayerBuffering, self.onBufferingEvent)
        self.__bufflastTime = 0
        
        self._playingStatus = PlayingStatus.STOPPED
        
        
        self.cache = cache
        self.queue: list[Song]
        self.pointer: int
        self.currentSongObject: Song
        
        self.purgetries = {}
    
    def onPlayEvent(self, event):
        print("Play Event")
        self._playingStatus = PlayingStatus.PLAYING
        self.playingStatusChanged.emit(self._playingStatus)
    
    def onPauseEvent(self, event):
        print("Pause Event")
        self._playingStatus = PlayingStatus.PAUSED
        self.playingStatusChanged.emit(self._playingStatus)
    
    def onBufferingEvent(self, event):
        if time.time() - self.__bufflastTime < 1:
            return
        self.__bufflastTime = time.time()
        self._playingStatus = PlayingStatus.BUFFERING
        self.playingStatusChanged.emit(self._playingStatus)

    @QProperty(bool, notify=playingStatusChanged)
    def isPlaying(self):
        with QMutexLocker(self._mutex):
            if self._playingStatus == PlayingStatus.PLAYING:
                return True
    
    @QProperty(int, notify=playingStatusChanged)
    def playingStatus(self):
        with QMutexLocker(self._mutex):
            if self.player.get_media() == None:
                return PlayingStatus.STOPPED
            
            return self._playingStatus
    
    @QProperty(list, notify=queueChanged)
    def queue(self):
        with QMutexLocker(self._queueAccessMutex):
            return self.queueModel._queue

    @queue.setter
    def queue(self, value):
        with QMutexLocker(self._queueAccessMutex):
            self.queueChanged.emit()
            self.setQueue(value, skipSetData=True)
            
    @QProperty(list, notify=queueChanged)
    def queueIds(self):
        with QMutexLocker(self._queueAccessMutex):
            return self.queueModel._queueIds

    @QProperty(str, notify=songChanged)
    def currentSongTitle(self):
        with QMutexLocker(self._mutex):
            return self.info(self.pointer)["title"]

    @QProperty(str, notify=songChanged)
    def currentSongChannel(self):
        with QMutexLocker(self._mutex):
            return self.info(self.pointer)["uploader"]

    @QProperty(str, notify=songChanged)
    def currentSongDescription(self):
        with QMutexLocker(self._mutex):
            return self.info(self.pointer)["description"]

    @QProperty(str, notify=songChanged)
    def currentSongId(self):
        return self.queueIds[self.pointer]

    @QProperty(QObject, notify=songChanged)
    def currentSongObject(self):
        return self.queue[self.pointer]

    @QProperty(int, notify=pointerMoved)
    def pointer(self):
        return self._pointer
        
    @pointer.setter
    def pointer(self, value):
        if value == -1:
            self._pointer = len(self.queue) - 1 # special case for setting pointer to last song
        if value < 0 or value >= len(self.queue):
            raise ValueError("Pointer must be between 0 and length of queue")
        
        self.pointerMoved.emit()
        self._pointer = value
        
    @QProperty(int, notify=songChanged)
    def currentSongDuration(self):
        try:
            return self.player.get_length() // 1000
        except OSError:
            return 0
        
    @QProperty(int, notify=songChanged)
    def currentSongTime(self):
        try:
            return self.player.get_time() // 1000
        except OSError:
            return 0
    
    @QProperty(int, notify=songChanged)
    def songFinishesAt(self):
        return time.time() + self.currentSongDuration - self.currentSongTime # current time + time left
        
    def checkError(self, url: str):
        r = requests.get(url)
        if r.status_code == 200:
            return False
        else:
            return True

    @Slot(result=dict)
    def getCurrentInfo(self) -> dict:
        return self.info(self.pointer)
    
    @Slot(str, bool)
    def setQueue(self, queue: list, skipSetData: bool = False):
        for i in queue:
            self.add(i)

    def songFinished(self, event):
        print("Song Finished")
        print(self.player.get_state())
        if self.loop == LoopType.SINGLE:
            self.play()
        elif self.loop == LoopType.ALL or self.loop == LoopType.NONE:
            self.next()
        else:
            print("LoopType Invalid")
            print("Treating as LoopType.NONE")
            self.next()
        self.songChanged.emit()
    
    def on_vlc_error(self, event):
        print("VLC Error")
        print(event)
        g.bgworker.add_job(self.refetch)
    
    def refetch(self):
        self.purgetries[self.queueIds[self.pointer]] = self.purgetries.get(self.queueIds[self.pointer], 0) + 1
        if self.purgetries[self.queueIds[self.pointer]] > 1:
            print("Purge Failed")
            self.stop()
            return
        else:
            self.queue[self.pointer].purge_playback()
        self.play()
    
    @Slot(str)
    def goToSong(self, id: str):
        if not id in self.queue:
            self.add(id)
        
        self.pointer = self.queueIds.index(id)
        self.play()
    
    @Slot()
    def pause(self):
        self.player.pause()
       
    @Slot()
    def resume(self):
        self.player.play()
        
         
    @Slot()
    def play(self):
        
        def Media(mrl):
            media: vlc.Media = self.instance.media_new(mrl)
            media.add_option("http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Herring/97.1.8280.8")
            media.add_option("http-referrer=https://www.youtube.com/")
            return media

        self.songChanged.emit()
        url = self.queue[self.pointer].get_best_playback_MRL()
        if not self.player.get_media() == None:
            self.player.stop()
            
        self.player.set_media(Media(url))
        self.player.play()
        self.durationChanged.emit()
    
    def migrate(self, MRL):
        """This function takes in a new MRL (for the same audio), and migrates the current song to that MRL, while trying to minimize interruptions.
        """
        paused = self.player.is_playing() == 0
        newMedia = self.instance.media_new(MRL)
        self.player.pause()
        t = self.player.get_time()
        self.player.set_media(newMedia)
        self.player.play() if not paused else self.player.pause()
        self.player.set_time(t)
        
    
    @Slot()
    def stop(self):
        self.player.stop()
    
    @Slot()
    def reload(self):
        self.play()
    
    @Slot(int)
    def setPointer(self, index: int):
        self.pointer = index
        self.reload()
    
    @Slot()
    def next(self):
        print("Next")
        print("Pointer: " + str(self.pointer), "Length: " + str(len(self.queue)))
        if self.pointer == len(self.queue) - 1:
            print("Queue Finished")
            if self.loop == LoopType.SINGLE:
                self.play() # pointer doesn't change, song doesn't change
                return
            elif self.loop == LoopType.ALL:
                self.pointer = 0
                self.play()
                return
            else:
                print("Queue Exhaused")
                self.stop()
                return
        
        self.pointer += 1
        self.play()
    
    @Slot()
    def prev(self):
        self.pointer = self.pointer - 1 if self.pointer > 0 else 0
        self.play()
    
    def info(self, pointer: int):
        if len(self.queue) == 0:
            return {
                "title": "No Songs",
                "uploader": "No Songs",
                "description": "No Songs"
            }

        song_ = self.queue[pointer]
        
        return {
            "title": song_.title,
            "uploader": song_.artist,
            "description": song_.description
        }
    
    def add(self, id: str, index: int = -1, goto: bool = False):
        s: Song = Song(id = id)
        coro = s.get_info(g.asyncBgworker.API)
        future = asyncio.run_coroutine_threadsafe(coro, g.asyncBgworker.event_loop)
        future.result() # wait for the result
        
        g.bgworker.add_job(self.finishAdd, s, index, goto)

    def finishAdd(self, song: Song, index: int = -1, goto: bool = False):
        song.get_playback()
        if index == -1:
            self.queueModel.insertRows(len(self.queue), 1)
            self.queueModel.setData(self.queueModel.index(len(self.queue) - 1), song, Qt.EditRole)
            self.queueIds.append(song.id)
        else:
            self.queueModel.insertRows(index, 1)
            self.queueModel.setData(self.queueModel.index(len(self.queue) - 1), song, Qt.EditRole)
            self.queueIds.insert(index, song.id)

        if goto:
            self.pointer = len(self.queue) -1 if index == -1 else index
            self.play()
    
    def _seek(self, seek_time: int):
        if seek_time < 0 or seek_time > self.player.get_length():
            raise ValueError("Time must be between 0 and video length")
        if not self.player.get_media() == None:
            self.player.set_time(seek_time)
            time.sleep(0.1) # wait for the buffer event to be emitted
            # override it
            self.onPlayEvent(None)
        else:
            raise ValueError("No Media Loaded")
    
    @Slot(int)
    def seek(self, time: int):
        """Absolute seek

        Args:
            time (int): Time to seek to in seconds
        """
        self._seek(time * 1000)
    
    @Slot(int)
    def aseek(self, time: int):
        """Relative seek

        Args:
            time (int): Time to move by in seconds (positive or negative)
        """
        self._seek(self.player.get_time() + time * 1000)
    
    @Slot(int)
    def pseek(self, percentage: int):
        """Percentage seek

        Args:
            percentage (int): The percentage of the video to seek to

        Raises:
            ValueError: If the percentage is not between 0 and 100
        """
        if percentage < 0 or percentage > 100:
            raise ValueError("Percentage must be between 0 and 100")
        self._seek(self.player.get_length() * percentage // 100)