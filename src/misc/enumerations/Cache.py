import enum

class EvictionMethod(enum.StrEnum):
    LRU = "lru"
    LFU = "lfu"
    Largest = "largest"
    
class Btypes(enum.StrEnum):
    BYTES = 'b'
    TEXT = ''
    AUTO = 'a'
    
class ErrorLevel(enum.IntEnum):
    INFO = 0
    WARNING = 1
    ERROR = 2