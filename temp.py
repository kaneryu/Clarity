import inspect
from PySide6.QtCore import QObject, Signal, Slot, Property
import time
from datetime import datetime, timedelta
import json
import asyncio
import io
import enum
import requests
from concurrent.futures import ThreadPoolExecutor
import ctypes

from PySide6.QtCore import QObject, Signal, Slot, Qt, Property as QProperty, QThread

import ytmusicapi as ytm
import yt_dlp as yt_dlp_module
import httpx

from src import universal as g
from src import cacheManager

ydlOpts = {
    "external_downloader_args": ['-loglevel', 'panic'],
    "quiet": False
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

class DownloadStatus(enum.Enum):
    NOT_DOWNLOADED = 0
    DOWNLOADING = 1
    DOWNLOADED = 2

class Song(QObject):
    
    idChanged = Signal(str)
    sourceChanged = Signal(str)
    downloadedChanged = Signal(bool)
    downloadStatusChanged = Signal(enum.Enum)
    downloadProgressChanged = Signal(int)
    
    _instances = {}
    
    def __new__(cls, id: str = "", givenInfo: dict = {"None": None}, cache: object = None):
        if id in cls._instances:
            return cls._instances[id]
        instance = super(Song, cls).__new__(cls, id, givenInfo)
        cls._instances[id] = instance
        return instance
    
    def __init__(self, id: str = "", givenInfo: dict = {"None": None}) -> None:
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
        
        self.moveToThread(g.mainThread)
    
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
    
    def from_search_result(self, search_result: dict) -> None:
        self.source = "search"
        
        self.title = search_result["title"]
        self.id = search_result["videoId"]
        
    async def get_info(self, api) -> None:
        """
        Gets the info of the song.
        """
        api: ytm.YTMusic = api
        print(self.id)
        c = cacheManager.getCache("songs_cache")
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
        self.largestThumbailUrl: str = self.largestThumbail["url"]
        
        self.views: int = int(self.rawVideoDetails["viewCount"])
        
        self.rawMicroformatData = self.rawData["microformat"]
        self.rectangleThumbnail: dict = self.rawMicroformatData["microformatDataRenderer"]["thumbnail"]["thumbnails"][-1]
        self.rectangleThumbnailUrl: str = self.rectangleThumbnail["url"]
        
        self.fullUrl: str = self.rawMicroformatData["microformatDataRenderer"]["urlCanonical"]
        self.description: bytes = self.rawMicroformatData["microformatDataRenderer"]["description"]
    
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

    def download_playbackInfo(self) -> None:
        """Because ytdlp isn't async, input this function into the BackgroundWorker to do the slow part in a different thread.
        """
        c = cacheManager.getCache("songs_cache")
        identifier = self.id + "_playbackinfo"
        self.rawPlaybackInfo = c.get(identifier)
        if not self.rawPlaybackInfo:
            self.rawPlaybackInfo = ytdl.extract_info(self.id, download=False)
            c.put(identifier, json.dumps(self.rawPlaybackInfo), byte = False, expiration = time.time() + 3600) # 1 hour
        else:
            self.rawPlaybackInfo = json.loads(self.rawPlaybackInfo)
        
        # self.rawPlaybackInfo = ytdl.extract_info(self.id, download=False)
        
        # open("playbackinfo.json", "w").write(json.dumps(self.rawPlaybackInfo))
        
    def get_playback(self):
        
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
        # print(self.playbackInfo)
    
    def purge_playback(self):
        c = cacheManager.getCache("songs_cache")
        identifier = self.id + "_playbackinfo"
        c.delete(identifier)
        self.rawPlaybackInfo = None
        
        self.get_playback()
    
        
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
            self.downloadStatus = DownloadStatus.DOWNLOADING
            try:
                print("Downloading", self.title)
            except:
                print("Downloading")
            
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
                    try:
                        self.downloadProgress = sum(self.downloadProgresses.values()) / total * 100
                    except ZeroDivisionError:
                        
                        self.downloadProgress = 0
                        
                await future
            print("Download complete")
            datastore.close_write_file(key=self.id, ext=ext, file=file)
            self.downloadStatus = DownloadStatus.DOWNLOADED
            self.downlaoded = True
            
    async def download(self, audio = True) -> None:
        """
        Downloads the song.
        """
        datastore = cacheManager.getdataStore("song_datastore")
        if not self.playbackInfo:
            self.get_playback()
        
        audio = self.playbackInfo["audio"]
        video = self.playbackInfo["video"]
        
        audio = audio[-1]
        video = video[-1]
        
        
        print(audio)
        if audio:
            url = audio["url"]
            ext = audio["ext"]
        else:
            url = video["url"]
            ext = video["ext"]
            
        if datastore.checkFileExists(self.id):
            datastore.delete(self.id)

        await self.download_with_progress(url, datastore, ext, self.id)
    
    
    def get_best_playback_MRL(self) -> str:
        """Will return either the path of the file on disk or best possbile quality playback URL.

        Returns:
            str: Path or URL
        """
        if self.downloaded or self.downloadStatus == DownloadStatus.DOWNLOADED:
            print("Asked for MRL; returning path")
            return cacheManager.getdataStore("song_datastore").getFilePath(self.id)
        else:
            if not self.playbackInfo:
                print("No playback info")
                return None
            print("Asked for MRL; returning URL")
            return self.playbackInfo["audio"][-1]["url"]
        
            
    async def get_lyrics(self, api) -> dict:
        """
        Gets the lyrics of the song.
        """
        api: ytm.YTMusic = api
        self.lyrics = await self.api.get_lyrics(self.id)
        return self.lyrics

class Test(QObject):
    def __init__(self):
        super().__init__()
        self._value = 0
    
    @Slot()
    def test(self):
        self.value += 1
        print(self.value)
    
    valueChanged = Signal()
    
    @Property(int, notify=valueChanged)
    def value(self):
        return self._value
    
    @value.setter
    def value(self, value):
        self._value = value
        self.valueChanged.emit()

class FwdVar:
    def __init__(self, getvar):
        self.var = getvar
        
    def __repr__(self):
        return self.var()
    
    def __str__(self):
        if isinstance(self.var(), str):
            return self.var()
        else:
            try:
                return str(self.var())
            except:
                return ""

class FakeQObj(QObject):
    def __init__(self, faking: object):
        super().__init__()
        self.using = faking
        usingCls = self.using.__class__
        
        inspected = inspect.getmembers(self.using)
        self.code: list[str] = inspect.getsource(usingCls).splitlines()
        
        for name, member in inspected:
            if name not in dir(QObject):
                if callable(member):
                    if isinstance(member, Property):
                        print("creating property " + name)
                        setattr(self, name, FwdVar(self.gvar(name)))
                    elif isinstance(member, Signal):
                        print("creating signal " + name)
                        self.createSignalAlias(name, member)
                    elif isinstance(member, Slot):
                        print("creating slot " + name)
                        setattr(self, name, self.funcforward(name))
                    else:
                        print("creaing function " + name)
                        setattr(self, name, self.funcforward(name))
                else:
                    try:
                        print("creating " + name, + member)
                    except:
                        print("creating " + name)
                    setattr(self, name, FwdVar(self.gvar(name)))
    
    def createSignalAlias(self, name, originalSignal: Signal):
        print("Creating signal alias for", name)

        # Complete Signal() code:
        # coolSignalName = Signal(str, "coolSignalName", ["arg1", "arg2"])
        
        # All are optional
        
        
        for index, line in enumerate(self.code):
            if line.strip().startswith("#"):
                continue
            
            if "Signal" in line and name in line:
                
                # Useful information in signals include the arguments, the type, and the name
                # The name is the easiest to get, as it's the name of the var, but the name in the signal is also important (QML uses it)
                
                sigline = line.strip()
                print(sigline)
                sigline = sigline[sigline.find("Signal"):]
                sigline = sigline.replace("Signal", "")
                sigline = sigline.lstrip("(").rstrip(")")
                sigline = sigline.split(",")
                

                sigtype = None
                signame = None
                sigargs = None
                
                if len(sigline) >= 1:
                    sigtype = sigline[0].strip()
                    # Now we check if the parsed type is real
                    try:
                        ev = eval("type(sigtype)")
                        if not isinstance(ev, object):
                            sigtype = None
                    except:
                        sigtype = None
                
                if len(sigline) >= 2:
                    signame = sigline[1].strip().removeprefix("\"").removesuffix("\"").removeprefix("\'").removesuffix("\'") # covers all cases
                if len(sigline) >= 3:
                    sigargs = sigline[2].strip()
                    if sigargs:
                        sigargs = json.loads(sigargs) # This is a list of strings
                        if not isinstance(sigargs, list):
                            sigargs = None
                            
        estr = "Signal("
        estr += sigtype if sigtype else ""
        estr += ", \"" + signame + "\"" if signame else ""
        estr += ", " + str(sigargs) if sigargs else ""
        estr += ")"
        
        aliasSignal = eval(estr)
        setattr(self.__class__, name, aliasSignal)
        originalSignal.connect(getattr(self, name).emit)
    
    def funcforward(self, name):
        def f(*args, **kwargs):
            return getattr(self.using, name)(*args, **kwargs)
        return f
    
    def gvar(self, name):
        def f():
            return getattr(self.using, name)
        return f
    
    def createPropGetter(self, name):
        def f():
            pass
        return f
    
    def createPropSetter(self, name):
        def f():
            pass
        return f
    
    def __dir__(self):
        return dir(self.using)

async def main():
    t: Song = FakeQObj(Song("SnxvXcLhdUw"))
    print(t.id)
    t.get_playback()
    print(t.playbackInfo)

    t.downloadProgressChanged.connect(lambda x: print(str(x) + "WAAU"))

    await t.download()
    
asyncio.run(main())