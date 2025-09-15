import enum

class LoopType(enum.Enum):
    """Loop Types"""
    NONE = 0  # Halt after playing all songs
    SINGLE = 1  # Repeat the current song
    ALL = 2  # Repeat all songs in the queue
