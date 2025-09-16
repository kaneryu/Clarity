import enum

class EvictionMethod(enum.StrEnum):
    """Cache Eviction Methods. Used to determine how to evict items from the cache when it is full.
    
    LRU: Least Recently Used \n
    LFU: Least Frequently Used \n
    Largest: Evict the largest items first \n
    
    """
    LRU = "lru"
    LFU = "lfu"
    Largest = "largest"
    
class Btypes(enum.StrEnum):
    """Data types for cache storage.
    
    BYTES: Store data as bytes \n
    TEXT: Store data as text \n
    AUTO: Automatically determine the type \n
    
    """
    BYTES = 'b'
    TEXT = ''
    AUTO = 'a'
    
class ErrorLevel(enum.IntEnum):
    """Error Levels. Used to indicate the severity of an error. (Cache related)
    
    INFO: Informational messages \n
    WARNING: Warning messages \n
    ERROR: Error messages \n
    
    """
    INFO = 0
    WARNING = 1
    ERROR = 2