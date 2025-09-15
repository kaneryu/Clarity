import enum

class PlayingStatus(enum.IntEnum):
    """Playing Status"""
    NOT_READY = -1  # Media is not ready to play
    PLAYING = 0  # Playing
    PAUSED = 1  # Paused
    BUFFERING = 2  # Media is buffering
    STOPPED = 3  # No media is loaded
    ERROR = 4  # Unrecoverable error
    
    NOT_PLAYING = 5  # Only for songproxy class; Returned when the current song is not currently playing

class DownloadStatus(enum.Enum):
    NOT_DOWNLOADED = 0
    DOWNLOADING = 1
    DOWNLOADED = 2