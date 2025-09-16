import enum

class DownloadStatus(enum.IntEnum):
    """Download Status for an Album.
    
    NONE_DOWNLOADED: No songs in the album are downloaded \n
    PARTIALLY_DOWNLOADED: Some songs in the album are downloaded \n
    DOWNLOAD_IN_PROGRESS: Some songs in the album are currently downloading \n
    FULLY_DOWNLOADED: All songs in the album are downloaded \n
    """
    NONE_DOWNLOADED = 0
    PARTIALLY_DOWNLOADED = 1
    DOWNLOAD_IN_PROGRESS = 2
    FULLY_DOWNLOADED = 3