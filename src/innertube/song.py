import ytmusicapi as ytm
import yt_dlp as yt_dlp_module

import time
from datetime import datetime, timedelta
import json

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

class Song:
    def __init__(self, id: str = "", givenInfo: dict = {"None": None}, cache: object = None) -> None:
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
        self.id = id
        self.source = None
        self.cache = cache
        
        self.rawPlaybackInfo = None
    
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
        if self.cache:
            c = self.cache.getCache("songs_cache")
            identifier = self.id + "_info"
            self.rawdata = c.get(identifier)
            if not self.rawdata:
                self.rawData: dict = await api.get_song(self.id)
                c.put(identifier, json.dumps(self.rawData), byte = False)
            else:
                self.rawData = json.loads(self.rawdata)
        else:
            self.rawData: dict = await api.get_song(self.id)
            

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
        c = self.cache.getCache("songs_cache")
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
        c = self.cache.getCache("songs_cache")
        identifier = self.id + "_playbackinfo"
        c.delete(identifier)
        self.rawPlaybackInfo = None
        
        self.get_playback()
        
            
    async def get_lyrics(self, api) -> dict:
        """
        Gets the lyrics of the song.
        """
        api: ytm.YTMusic = api
        self.lyrics = await self.api.get_lyrics(self.id)
        return self.lyrics