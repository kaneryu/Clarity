from typing import Optional, List, Dict, Any
import dataclasses

import dacite

from src.providerInterface.globalModels import (
    SimpleIdentifier,
    NamespacedIdentifier,
    NamespacedTypedIdentifier,
)

"""
Preliminary Spec.
This is currently strongly associated to youtube
In the future, the association will be weaker.
"""


class songDataDict(dict):
    """
    A specialized dictionary type for song data.
    """

    pass


class rawSongDataDict(dict):
    """
    A specialized dictionary type for raw song data.
    """

    pass


@dataclasses.dataclass
class ThumbnailEntry:
    url: str
    width: Optional[int] = None
    height: Optional[int] = None


@dataclasses.dataclass
class ThumbnailSet:
    thumbnails: List[ThumbnailEntry] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class PageOwnerDetails:
    name: Optional[str] = None
    externalChannelId: Optional[str] = None
    youtubeProfileUrl: Optional[str] = None


@dataclasses.dataclass
class VideoDetails:
    videoId: Optional[str] = None
    title: Optional[str] = None
    lengthSeconds: Optional[int] = (
        None  # original JSON uses string, convert/parse if needed
    )
    channelId: Optional[str] = None
    author: Optional[str] = None
    viewCount: Optional[int] = None
    isPrivate: Optional[bool] = None
    isLiveContent: Optional[bool] = None
    allowRatings: Optional[bool] = None
    thumbnail: Optional[ThumbnailSet] = None
    # catch-all for other keys
    extra: Dict[str, Any] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class PlaybackUrlHeader:
    headerType: Optional[str] = None


@dataclasses.dataclass
class PlaybackUrl:
    baseUrl: Optional[str] = None
    headers: List[PlaybackUrlHeader] = dataclasses.field(default_factory=list)
    elapsedMediaTimeSeconds: Optional[int] = None


@dataclasses.dataclass
class PlaybackTracking:
    videostatsPlaybackUrl: Optional[PlaybackUrl] = None
    videostatsDelayplayUrl: Optional[PlaybackUrl] = None
    videostatsWatchtimeUrl: Optional[PlaybackUrl] = None
    ptrackingUrl: Optional[PlaybackUrl] = None
    qoeUrl: Optional[PlaybackUrl] = None
    atrUrl: Optional[PlaybackUrl] = None
    videostatsScheduledFlushWalltimeSeconds: List[int] = dataclasses.field(
        default_factory=list
    )
    videostatsDefaultFlushIntervalSeconds: Optional[int] = None
    # catch-all
    extra: Dict[str, Any] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class MicroformatDataRenderer:
    urlCanonical: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    thumbnail: Optional[ThumbnailSet] = None
    siteName: Optional[str] = None
    appName: Optional[str] = None
    ogType: Optional[str] = None
    tags: List[str] = dataclasses.field(default_factory=list)
    availableCountries: List[str] = dataclasses.field(default_factory=list)
    pageOwnerDetails: Optional[PageOwnerDetails] = None
    videoDetails: Dict[str, Any] = dataclasses.field(default_factory=dict)
    viewCount: Optional[int] = None
    publishDate: Optional[str] = None
    uploadDate: Optional[str] = None
    category: Optional[str] = None
    # catch-all
    extra: Dict[str, Any] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class SongData:
    id: SimpleIdentifier

    source: str = "full"

    # core identity
    title: Optional[str] = None
    duration: Optional[int] = None

    # artists / channel info
    author: Optional[str] = None
    artist: Optional[str] = None
    channel: Optional[str] = None
    channelId: Optional[str] = None
    artistId: Optional[str] = None

    # thumbnails (rich typed)
    thumbnails: Optional[Dict[str, Any]] = dataclasses.field(default_factory=dict)
    smallestThumbnail: Optional[Dict[str, Any]] = dataclasses.field(
        default_factory=dict
    )
    largestThumbnail: Optional[Dict[str, Any]] = dataclasses.field(default_factory=dict)
    smallestThumbnailUrl: Optional[str] = None
    largestThumbnailUrl: Optional[str] = None

    # original rectangle thumbnail block / url
    rectangleThumbnail: Optional[Dict[str, Any]] = dataclasses.field(
        default_factory=dict
    )
    rectangleThumbnailUrl: Optional[str] = None

    # urls / description / metadata
    fullUrl: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = dataclasses.field(default_factory=list)

    # counts / flags
    views: Optional[int] = None
    isFamilySafe: Optional[bool] = None
    allowRatings: Optional[bool] = None

    # owner / page info
    pageOwnerDetails: Optional[PageOwnerDetails] = None
    pageOwnerName: Optional[str] = None
    pageOwnerChannelId: Optional[str] = None

    # dates / timestamps
    uploadDate: Optional[str] = None
    publishDate: Optional[str] = None
    uploadDateTimestamp: Optional[float] = None
    publishDateTimestamp: Optional[float] = None

    category: Optional[str] = None

    # nested rich structures from JSON
    playabilityStatus: Optional[Dict[str, Any]] = dataclasses.field(
        default_factory=dict
    )
    playbackTracking: Optional[PlaybackTracking] = None
    videoDetails: Optional[VideoDetails] = None
    microformat: Optional[MicroformatDataRenderer] = None

    # preserve any extra fields present
    extra: Dict[str, Any] = dataclasses.field(default_factory=dict)

    @staticmethod
    def from_dict(data: songDataDict) -> "SongData":
        """
        Create a SongData instance from a dictionary.

        NOTE: The data *MUST* have been created from a SongData instance originally.
        This means that if you're getting raw data from the server, DO NOT use it with this method
        Instead, use the provider's parsing methods to first sanitize/convert the raw data into a SongData instance.

        The main use for this is loading from cached data that was stored as a dictionary.
        """
        return dacite.from_dict(
            data_class=SongData,
            data=data,
            config=dacite.Config(
                cast=[str, SimpleIdentifier]
            ),  # pretty self explanatory, but this ensures that str IDs are converted to SimpleIdentifier instances
        )

    def as_dict(self) -> Dict[str, Any]:
        """
        Convert the SongData instance to a dictionary.
        """
        data = dataclasses.asdict(self)
        data["id"] = str(data["id"])  # ensure SimpleIdentifier is converted to string
        return data
