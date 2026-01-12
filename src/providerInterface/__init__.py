from src.providerInterface.song import (
    Song,
    SongProxy,
    SongImageProvider,
    PlayingStatus,
    SongListModel,
    SongProxyListModel,
)
from src.providerInterface.search import (
    search,
    search_suggestions,
    BasicSearchResultsModel,
)
from src.misc.enumerations.Search import SearchFilters

from src.providerInterface.globalModels import (
    SimpleIdentifier,
    NamespacedIdentifier,
    NamespacedTypedIdentifier,
)

"""
This is a module for song, album, playlist, and any other music-related entities.

Current submodules:
search.py - search for a song
song.py - stores the class for a song
testing.py - internal file for testing future features (not unit tests)
"""
__all__ = [
    "Song",
    "SongProxy",
    "SongImageProvider",
    "search",
    "search_suggestions",
    "SearchFilters",
    "BasicSearchResultsModel",
    "PlayingStatus",
    "SongListModel",
    "SongProxyListModel",
    "SimpleIdentifier",
    "NamespacedIdentifier",
    "NamespacedTypedIdentifier",
]
