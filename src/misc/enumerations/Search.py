import enum


class SearchFilters(enum.StrEnum):
    """Search Filters. Used in search queries to filter results."""

    SONGS = "songs"
    VIDEOS = "videos"
    ALBUMS = "albums"
    ARTISTS = "artists"
    PLAYLISTS = "playlists"
    COMMUNITY_PLAYLISTS = "community_playlists"
    FEATURED_PLAYLISTS = "featured_playlists"
    UPLOADS = "uploads"
