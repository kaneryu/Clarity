import json
import os
from typing import Optional, Any, Union, Dict

import ytmusicapi as ytm
import yt_dlp as yt_dlp_module  # type: ignore[import-untyped]

from src import universal as universal
from src import cacheManager
from src.providerInterface.song.providers.youtube.constants import ydlOpts
from src.providerInterface.song.providers.youtube.utils import (
    playback_from_raw,
    songdata_from_raw,
)
from src.misc.enumerations.Song import DownloadState

from src.providerInterface.song.models import (
    SongData,
    PlaybackData,
    rawPlaybackDataDict,
    rawSongDataDict,
    Lyrics,
    TimedLyrics,
)
from src.providerInterface.globalModels.identifier import (
    SimpleIdentifier,
    NamespacedIdentifier,
    NamespacedTypedIdentifier,
)

from src.providerInterface.song.providers.providerInterface import ProviderInterface

ytdl: yt_dlp_module.YoutubeDL
ytdl = yt_dlp_module.YoutubeDL(ydlOpts)

logger = universal.logger.getChild("YoutubeProvider")

SimpleIdentifier_or_Str = Union[SimpleIdentifier, str]


class YoutubeProvider(ProviderInterface):
    """
    YouTube provider implementation.
    """

    NAME = "youtube"

    CACHE = cacheManager.CacheManager(
        "youtube", os.path.join(universal.Paths.DATAPATH, "providers", "youtubeCache")
    )
    DATASTORE = cacheManager.DataStore(
        "youtube",
        os.path.join(universal.Paths.DATAPATH, "providers", "youtubeDataStore"),
        "songDonwnloads",
    )

    @staticmethod
    def convert_to_namespaced_id(
        provider_id: SimpleIdentifier_or_Str,
    ) -> NamespacedTypedIdentifier:
        return NamespacedTypedIdentifier(
            namespacedIdentifier=NamespacedIdentifier(
                namespace=YoutubeProvider.NAME,
                id=(
                    provider_id
                    if isinstance(provider_id, SimpleIdentifier)
                    else SimpleIdentifier(id=provider_id)
                ),
            ),
            type=YoutubeProvider.TYPE,
        )

    @staticmethod
    async def get_info(provider_id: SimpleIdentifier_or_Str) -> Optional[SongData]:
        """
        Gets the info of the song.
        """
        api: ytm.YTMusic = universal.asyncBgworker.API

        if isinstance(provider_id, SimpleIdentifier):
            provider_id = provider_id.id

        rawData = await api.get_song(provider_id)
        if rawData.get("playabilityStatus", {}).get("status") == "ERROR":
            logger.warning(
                f"Song cannot be retrieved due to playability issues. id: {provider_id} "
                + rawData.get("playabilityStatus", {}).get("reason")
            )
            return None
        if rawData.get("playabilityStatus", {}).get("status") == "LOGIN_REQUIRED":
            logger.warning(
                f"Song cannot be retrieved due to login requirements. id: {provider_id} "
                + rawData.get("playabilityStatus", {}).get("reason")
            )
            return None

        album = await api.get_song_album_id(provider_id)

        return songdata_from_raw(rawData, album)

    @staticmethod
    def get_playback(
        provider_id: SimpleIdentifier_or_Str, skip_download: bool = False
    ) -> Optional[PlaybackData]:

        if isinstance(provider_id, SimpleIdentifier):
            provider_id = provider_id.id

        playbackinfo = ytdl.extract_info(provider_id, download=False)

        if playbackinfo is None:
            logger.error(
                "Failed to get playback info, probably due to network reasons."
            )
            return None

        return playback_from_raw(playbackinfo)

    @staticmethod
    async def get_lyrics(
        provider_id: SimpleIdentifier_or_Str,
    ) -> Optional[Union[Lyrics, TimedLyrics]]:
        """
        Gets the lyrics of the song.
        """
        if isinstance(provider_id, SimpleIdentifier):
            provider_id = provider_id.id

        return await universal.asyncBgworker.API.get_lyrics(provider_id)

    @staticmethod
    def from_search_result(search_result: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    @staticmethod
    def song_data_from_raw(raw_data: rawSongDataDict) -> Optional[SongData]:
        return songdata_from_raw(raw_data)

    @staticmethod
    def playback_from_raw(raw_data: rawPlaybackDataDict) -> Optional[PlaybackData]:
        return playback_from_raw(raw_data)
