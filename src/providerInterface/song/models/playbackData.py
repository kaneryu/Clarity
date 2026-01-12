from typing import Union, Optional, List, Dict, Any
from dataclasses import dataclass, field
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


class playbackDataDict(dict):
    """
    A specialized dictionary type for playback data.
    """

    pass


class rawPlaybackDataDict(dict):
    """
    A specialized dictionary type for raw playback data.
    """

    pass


@dataclass(frozen=True, eq=True)
class DataFragment:
    url: str
    duration: float


@dataclass(frozen=True, eq=True)
class FormatData:
    url: str = ""
    clarity_quality: int = 0

    ext: Optional[str] = None

    audio: bool = True  # is this an audio format, false for video


@dataclass(frozen=True, eq=True)
class YoutubeFormatData(FormatData):

    format_id: Optional[str] = None
    format_note: Optional[str] = None
    source_preference: Optional[int] = None
    ext: Optional[str] = None
    protocol: Optional[str] = None
    acodec: Optional[str] = None
    vcodec: Optional[str] = None

    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    rows: Optional[int] = None
    columns: Optional[int] = None

    fragments: Optional[List[DataFragment]] = None

    audio_ext: Optional[str] = None
    video_ext: Optional[str] = None
    vbr: Optional[float] = None
    abr: Optional[float] = None
    tbr: Optional[float] = None
    resolution: Optional[str] = None
    aspect_ratio: Optional[float] = None
    filesize_approx: Optional[int] = None
    filesize: Optional[int] = None
    http_headers: Optional[Dict[str, str]] = None

    format: Optional[str] = None

    # Additional common fields present in various formats
    asr: Optional[int] = None
    audio_channels: Optional[int] = None
    quality: Optional[float] = None
    has_drm: Optional[bool] = None
    available_at: Optional[int] = None
    downloader_options: Optional[Dict[str, Any]] = None
    container: Optional[str] = None
    dynamic_range: Optional[str] = None
    manifest_url: Optional[str] = None
    manifest_index: Optional[int] = None
    preference: Optional[int] = None

    # catch-all for unexpected keys
    extra: Dict[str, Any] = field(default_factory=dict)


fmtDataType = Union[FormatData, YoutubeFormatData]


@dataclass(frozen=True, eq=True)
class Thumbnail:
    url: str
    height: Optional[int] = None
    width: Optional[int] = None
    preference: Optional[int] = None
    id: Optional[Union[int, str]] = None
    resolution: Optional[str] = None


# new dataclass for heatmap entries
@dataclass(frozen=True, eq=True)
class HeatmapEntry:
    start_time: float
    end_time: float
    value: float


@dataclass(frozen=True, eq=True)
class PlaybackData(rawPlaybackDataDict):

    id: SimpleIdentifier
    title: Optional[str] = None

    formats: Optional[List[FormatData]] = None

    audio_formats: Optional[List[FormatData]] = None
    video_formats: Optional[List[FormatData]] = None

    from_download: Optional[bool] = None

    @staticmethod
    def get_best_audio_format(playback_data: "PlaybackData") -> Optional[FormatData]:
        """
        Utility method to get the best audio format from the playback data.
        """
        if not playback_data.formats:
            return None
        audio_formats = [fmt for fmt in playback_data.formats if fmt.audio]
        if not audio_formats:
            return None

        audio_formats.sort(
            key=lambda x: (x.clarity_quality if x.clarity_quality is not None else 0),
            reverse=True,
        )

        if type(audio_formats[0]) is not FormatData:
            if getattr(audio_formats[0], "clarity_quality") is not None:
                best_format = audio_formats[0]
                return FormatData(
                    url=best_format.url,
                    audio=True,
                    ext=best_format.ext,
                    clarity_quality=best_format.clarity_quality,
                )
            else:
                raise TypeError(
                    "Audio format is not of type FormatData, check the implementation of the provider."
                )
        else:
            return audio_formats[0]

    @staticmethod
    def from_dict(data: playbackDataDict) -> "PlaybackData":
        """
        Create a PlaybackData instance from a dictionary.
        NOTE: The data *MUST* have been created from a PlaybackData instance originally.
        This means that if you're getting raw data from the server, DO NOT use it with this method
        Instead, use the provider's parsing methods to first sanitize/convert the raw data into a PlaybackData instance.

        The main use for this is loading from cached data that was stored as a dictionary.
        """
        return dacite.from_dict(
            data_class=PlaybackData,
            data=data,
            config=dacite.Config(cast=[str, SimpleIdentifier]),
        )

    def as_dict(self) -> playbackDataDict:
        """
        Convert the PlaybackData instance to a dictionary.
        """
        data = dataclasses.asdict(self)
        data["id"] = str(data["id"])  # ensure SimpleIdentifier is converted to string
        return data


# top-level playback data
@dataclass(frozen=True, eq=True)
class YoutubePlaybackData(PlaybackData):

    requested_formats: Optional[List[fmtDataType]] = None
    rawFormats: Optional[List[Dict[str, Any]]] = None

    thumbnails: Optional[List[Thumbnail]] = None
    thumbnail: Optional[str] = None

    description: Optional[str] = None

    channel_id: Optional[str] = None
    channel_url: Optional[str] = None
    channel: Optional[str] = None
    channel_follower_count: Optional[int] = None
    channel_is_verified: Optional[bool] = None

    duration: Optional[int] = None
    duration_string: Optional[str] = None
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    comment_count: Optional[int] = None

    average_rating: Optional[float] = None
    age_limit: Optional[int] = None

    webpage_url: Optional[str] = None
    webpage_url_basename: Optional[str] = None
    webpage_url_domain: Optional[str] = None
    original_url: Optional[str] = None
    fulltitle: Optional[str] = None
    display_id: Optional[str] = None

    categories: Optional[List[str]] = None
    tags: Optional[List[str]] = None

    playable_in_embed: Optional[bool] = None
    live_status: Optional[str] = None
    is_live: Optional[bool] = None
    was_live: Optional[bool] = None
    media_type: Optional[str] = None

    release_timestamp: Optional[int] = None
    release_date: Optional[str] = None
    release_year: Optional[int] = None
    album: Optional[str] = None
    artists: Optional[List[str]] = None
    track: Optional[str] = None

    automatic_captions: Optional[Dict[str, Any]] = None
    subtitles: Optional[Dict[str, Any]] = None
    chapters: Optional[Any] = None

    heatmap: Optional[List[HeatmapEntry]] = None

    uploader: Optional[str] = None
    uploader_id: Optional[str] = None
    uploader_url: Optional[str] = None
    upload_date: Optional[str] = None
    timestamp: Optional[int] = None
    epoch: Optional[int] = None

    creators: Optional[List[str]] = None
    artist: Optional[str] = None
    creator: Optional[str] = None
    alt_title: Optional[str] = None

    availability: Optional[str] = None
    extractor: Optional[str] = None
    extractor_key: Optional[str] = None
    extractor_id: Optional[str] = None

    format: Optional[str] = None
    format_id: Optional[str] = None
    format_note: Optional[str] = None
    ext: Optional[str] = None
    protocol: Optional[str] = None
    filesize_approx: Optional[int] = None
    tbr: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    resolution: Optional[str] = None
    fps: Optional[float] = None
    dynamic_range: Optional[str] = None
    vcodec: Optional[str] = None
    vbr: Optional[float] = None
    acodec: Optional[str] = None
    abr: Optional[float] = None
    asr: Optional[int] = None
    audio_channels: Optional[int] = None

    # any additional keys preserved
    extra: Dict[str, Any] = field(default_factory=dict)
