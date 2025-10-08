import enum


class OnlineStatus(enum.IntEnum):
    """Online Status. Used to indicate the current online status of the application.

    OFFLINE: No internet connection \n
    ONLINE: Online with YouTube access \n
    ONLINE_NO_YOUTUBE: Online without YouTube access (e.g., YouTube is blocked) \n

    """

    OFFLINE = 0
    ONLINE = 1
    ONLINE_NO_YOUTUBE = 2
