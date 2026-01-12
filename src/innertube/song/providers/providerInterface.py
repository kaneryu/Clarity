from typing import Optional, Dict, Any, runtime_checkable, Protocol, Union
from collections.abc import Callable

from src.innertube.song.models import (
    SongData,
    PlaybackData,
    Lyrics,
    TimedLyrics,
    rawSongDataDict,
    rawPlaybackDataDict,
)

from src.innertube.globalModels.identifier import (
    SimpleIdentifier,
    NamespacedIdentifier,
    NamespacedTypedIdentifier,
)

from src.cacheManager import CacheManager, DataStore

"""
Providers should always be asynchronous where possible to avoid blocking the main event loop.
Providers should be stateless. They should always data, then the parent Song class will handle updating state as needed.
Providers do not need to handle storing any data. The only exception is when downloading files to the datastore. (This means that the parent song class will handle caching, etc.)
"""

SimpleIdentifier_or_Str = Union[SimpleIdentifier, str]


@runtime_checkable
class ProviderInterface(Protocol):
    """
    Minimal interface a provider must satisfy to be pluggable where the current YouTube-backed Song expects parity.
    Implementations should use universal.bgworker / universal.asyncBgworker for blocking IO and cacheManager/datastore for persistence.
    """

    NAME: str

    TYPE: str = "song"

    CACHE: CacheManager
    DATASTORE: DataStore

    @staticmethod
    def convert_to_namespaced_id(
        provider_id: SimpleIdentifier_or_Str,
    ) -> NamespacedTypedIdentifier:
        """
        Convert provider-specific ID to namespaced ID in the format provider:type:provider_id
        """
        ...

    @staticmethod
    async def get_info(provider_id: SimpleIdentifier_or_Str) -> Optional[SongData]:
        """
        Fetch and return full metadata for `id`.
        - Use cache key: f"{id}_info" in songs_cache.
        - Populate/return a dict containing at least: videoId/id, title, lengthSeconds/duration, author/artist, thumbnail info, microformat-like fields.
        - Should raise / return sensible value when playability/login issues occur.
        """
        ...

    @staticmethod
    def get_playback(
        provider_id: SimpleIdentifier_or_Str, skip_download: bool = False
    ) -> Optional[PlaybackData]:
        """
        Build the normalized playbackInfo: {'audio': [...], 'video': [...]}
        - Use raw playback extraction or datastore file metadata if downloaded.
        - Each item must include keys: format_id, ext, url, quality, qualityName, filesize, type ('audio'|'video').
        """
        ...

    @staticmethod
    async def get_lyrics(
        provider_id: SimpleIdentifier_or_Str,
    ) -> Optional[Union[Lyrics, TimedLyrics]]:
        """
        Provider lyric fetch if supported. Return lyrics or None.
        """
        ...

    @staticmethod
    def from_search_result(search_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a search result into minimal metadata: { 'id': ..., 'title': ..., 'source': 'search', ... }
        """
        ...

    @staticmethod
    def song_data_from_raw(raw_data: rawSongDataDict) -> Optional[SongData]:
        """
        Convert raw provider data to SongData.
        """
        ...

    @staticmethod
    def playback_from_raw(raw_data: rawPlaybackDataDict) -> Optional[PlaybackData]:
        """
        Convert raw provider playback data to PlaybackData.
        """
        ...
