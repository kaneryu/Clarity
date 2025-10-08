from src.innertube.song import Song
from src.innertube.search import search, search_suggestions, BasicSearchResultsModel
from src.misc.enumerations.Search import SearchFilters

"""
This is a wrapper around ytmusicapi and youtube-dl.

Current submodules:
search.py - search for a song
song.py - stores the class for a song
testing.py - internal file for testing future features (not unit tests)
"""
__all__ = [
    "Song",
    "search",
    "search_suggestions",
    "SearchFilters",
    "BasicSearchResultsModel",
]
