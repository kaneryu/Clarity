import ytmusicapi as ytm
import time
from datetime import datetime, timedelta

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
    def __init__(self, yt_id: str = "", autoGetInfo: bool = False, givenInfo: dict = {"None": None}):
        """
        A class that represents a youtube music song.
        To actually get the info of the song, use the get_info_short or get_info_full method after initializing the class, or set auto_get_info to True.
        
        Parameters:
        yt_id (str): The id of the youtube video.
        autoGetInfo (bool): Whether to automatically get the info of the song or not. Uses the get_info_short method.
        
        Functions:
        get_info_short: Gets the basic info of the song.
        get_info_full: Gets the full info of the song.
        get_lyrics: Gets the lyrics of the song.
        """
        self.id = yt_id
        self.source = None
    
    def from_search_result(self, search_result: dict) -> None:
        self.source = "search"
        
        self.title = search_result["title"]
        self.id = search_result["videoId"]
        
    async def get_info(self, api, cache: object) -> None:
        """
        Gets the info of the song.
        """
        api: ytm.YTMusic = api
        
        if cache:
            c = cache.getCache("songs_cache")
            identifier = self.id + "_info"
        
        self.rawdata = await c.get(identifier)
        if not self.rawdata:
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
        
    async def get_lyrics(self, api) -> dict:
        """
        Gets the lyrics of the song.
        """
        api: ytm.YTMusic = api
        self.lyrics = await self.api.get_lyrics(self.id)
        return self.lyrics