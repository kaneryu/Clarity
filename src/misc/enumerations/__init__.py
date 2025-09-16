# from .CacheEnums import *
# from .NetworkingEnums import *
import enum

class DataStatus(enum.Enum):
    """ The status of the data for this class. Used in various classes, typically in ones fetched from youtube
    
    NOTLOADED: The data hasn't been downloaded or set at all \n
    LOADING: The data is downloading or being set \n
    LOADED: The data is downloaded and set \n
    ERROR: There was an error downloading or fetching the data, expect no data to be available \n
    
    """
    NOTLOADED = 0
    LOADING = 1
    LOADED = 2
    ERROR = 3