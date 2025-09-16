import enum

class PlayingStatus(enum.IntEnum):
    """Playing Status. Used to indicate the current playing status of a song.
    
    NOT_READY: Media is not ready to play \n
    PLAYING: Playing \n
    PAUSED: Paused \n
    BUFFERING: Media is buffering \n
    STOPPED: No media is loaded \n
    ERROR: Unrecoverable error \n
    NOT_PLAYING: Only for songproxy class; Returned when the current song is not currently playing \n
    
    """
    NOT_READY = -1  # Media is not ready to play
    PLAYING = 0  # Playing
    PAUSED = 1  # Paused
    BUFFERING = 2  # Media is buffering
    STOPPED = 3  # No media is loaded
    ERROR = 4  # Unrecoverable error
    
    NOT_PLAYING = 5  # Only for songproxy class; Returned when the current song is not currently playing

class DownloadStatus(enum.IntEnum):
    """ Download Status. Used to indicate the download status of a song.
    
    NOT_DOWNLOADED: The song is not downloaded \n
    DOWNLOADING: The song is currently downloading \n
    DOWNLOADED: The song is fully downloaded \n
    
    """
    NOT_DOWNLOADED = 0
    DOWNLOADING = 1
    DOWNLOADED = 2