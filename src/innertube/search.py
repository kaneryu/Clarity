"""
Search.
"""


import enum
import json
from typing import Union
import asyncio
import song



class Base:
    def __init__(self, item: dict):
        for key, value in item.items():
            setattr(self, key, value)

class Video(Base):
    def __init__(self, item: dict):
        super().__init__(item)

class Album(Base):
    def __init__(self, item: dict):
        super().__init__(item)

class Artist(Base):
    def __init__(self, item: dict):
        super().__init__(item)

class Playlist(Base):
    def __init__(self, item: dict):
        super().__init__(item)

class Podcast(Base):
    def __init__(self, item: dict):
        super().__init__(item)

class Episode(Base):
    def __init__(self, item: dict):
        super().__init__(item)

searchResultItem = Union[song.Song, Video, Album, Artist, Playlist, Podcast, Episode]

def get_search_result_item(item: dict) -> searchResultItem:
    category = item["category"]
    if category == "Episodes":
        return Episode(item)
    if category == "Podcasts":
        return Podcast(item)
    if category == "Songs":
        item_ = song.Song()
        item_.from_search_result(item)
        return item_
    if category == "Profiles":
        return Artist(item)
    if category == "Playlists":
        return Playlist(item)
    if category == "Albums":
        return Album(item)
    if category == "Videos":
        return Video(item)

class searchFilters(enum.StrEnum):
    SONGS = "songs"
    VIDEOS = "videos"
    ALBUMS = "albums"
    ARTISTS = "artists"
    PLAYLISTS = "playlists"
    COMMUNITY_PLAYLISTS = "community_playlists"
    FEATURED_PLAYLISTS = "featured_playlists"
    UPLOADS = "uploads"

async def search_suggestions(query: str, detailed = True) -> list | dict:
    """Will return the text that shows up while you are typing a search query in youtube music.

    Args:
        query (str): The query to search for.

    Returns:
        list: A list of suggestions.
        detailed: A dictionary of suggestions, with more details.
    """
    
    return await API.get_search_suggestions(query, detailed_runs = detailed)

async def search(query: str, filter: searchFilters = searchFilters.SONGS, limit: int = 20, ignore_spelling: bool = False) -> list[searchResultItem]:
    """Searches youtube music

    Args:
        query (str): The query to search for.
        filter (str, optional): The filter to use. Defaults to songs, use the searchFilters enum.
        max_results (int, optional): Maximum results. Defaults to 20.

    Returns:
        searchResult: A class that contains the results.
    """
    list = []
    for result in await API.search(query, filter = filter, limit = limit, ignore_spelling = ignore_spelling):
        list.append(get_search_result_item(result))
    return list

async def main():
    global API
    API = ytmusicapi.YTMusic()
    st = await search("hello") # Returns a list of searchResultItem objects.
    print(st[0].title) # Returns the title of the first search result.
    await API.close()
    
asyncio.run(main())