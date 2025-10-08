import enum


class LoopType(enum.IntEnum):
    """Loop Types. Used to indicate the current loop type of the queue.

    NONE: Halt after playing all songs \n
    SINGLE: Repeat the current song \n
    ALL: Repeat all songs in the queue \n

    """

    NONE = 0  # Halt after playing all songs
    SINGLE = 1  # Repeat the current song
    ALL = 2  # Repeat all songs in the queue
