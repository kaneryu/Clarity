"""
Search.
"""

import ytmusicapi
import enum
import json

API = ytmusicapi.YTMusic()

class searchResultItem:
    pass

class searchFilters(enum.StrEnum):
    SONGS = "songs"
    VIDEOS = "videos"
    ALBUMS = "albums"
    ARTISTS = "artists"
    PLAYLISTS = "playlists"
    COMMUNITY_PLAYLISTS = "community_playlists"
    FEATURED_PLAYLISTS = "featured_playlists"
    UPLOADS = "uploads"

def search_suggestions(query: str, detailed = True) -> list | dict:
    """Will return the text that shows up while you are typing a search query in youtube music.

    Args:
        query (str): The query to search for.

    Returns:
        list: A list of suggestions.
        detailed: A dictionary of suggestions, with more details.
    """
    
    return API.get_search_suggestions(query, detailed_runs = detailed)

def search(query: str, filter: searchFilters = searchFilters.SONGS, max_results: int = 20) -> list[searchResultItem]:
    """Searches youtube music

    Args:
        query (str): The query to search for.
        filter (str, optional): The filter to use. Defaults to songs, use the searchFilters enum.
        max_results (int, optional): Maximum results. Defaults to 20.

    Returns:
        searchResult: A class that contains the results.
    """
    
    
    
    return [searchResultItem()]

