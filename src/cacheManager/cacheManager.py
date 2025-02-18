"""Global cache manager for the application.
    Both async and sync cache functions are available.
"""
import asyncio
import time
from typing import Any, Optional
import os
from PIL import Image
import json
import collections
import concurrent.futures
import enum
from hashlib import md5

def ghash(thing):
    # print("making hash for", thing, ":", md5(str(thing).encode()).hexdigest())
    return md5(str(thing).encode()).hexdigest()

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

caches = {}

def cacheExists(name: str) -> bool:
    """Check if a cache exists

    Args:
        name (str): The name of the cache

    Returns:
        bool: Whether or not the cache exists
    """
    return name in caches

def getCache(name: str) -> "CacheManager":
    """Get a cache by name

    Args:
        name (str): The name of the cache

    Returns:
        CacheManager: The cache
    """
    return caches.get(name)

def run_sync(coro):
    def run_in_thread(loop, coro):
        asyncio.set_event_loop(loop)
        loop.run_until_complete(coro)

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_in_thread, asyncio.new_event_loop(), coro)
            return future.result()
    else:
        return asyncio.run(coro)
    
class CustomLock:
    def __init__(self):
        self.lock = False
    
    def __enter__(self):
        if self.lock:
            while self.lock:
                time.sleep(1/15)
            # at this point, the lock is free
            self.lock = True
        
    
    def __exit__(self, *args):
        self.lock = False
        
class CacheManager:
    def __init__(self, name: str, directory: str = ""):
        """Initialize the CacheManager.
        Note that this cache is persistent only
        Args:
            directory (str): Directory to store semi-persistent cache files.
            name (str): Name for the cache.
        """
        self.max_size = 1000000000 # 1GB
        self.__cache_path_map = {}
        self.metadata: dict[str, dict] = {}
        self.last_used = collections.OrderedDict()
        self.name = name or ""
        self.event_loop = asyncio.get_event_loop()
        if directory == "":
            self.directory = f"{os.pathsep}{name}-cache" if not "cache" in name.lower() else f".{os.pathsep}{name}"
        else:
            self.directory = directory
            
        self.lock = CustomLock()
        self.plevel = ErrorLevel.WARNING
        
        self.statistics = {
            "hits": 0,
            "misses": 0,
            "saves": 0,
            "evictons": 0, # keeps track of how many items have been evicted
            "deletions": 0, # keeps track of how many items have been deleted, including evictions
            "size": 0
        }
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
        
        self.absdir = os.path.abspath(self.directory)
        
        caches[name] = self
        
        if not self.__metadataLoad():
            self.__metadataSave()
            
    def ordered_dict_to_dict(self, obj):
        if isinstance(obj, collections.OrderedDict):
            return dict(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    def __metadataSave(self):
        """Internal function, saves metadata.
        """
        cpm = json.dumps(self.__cache_path_map)
        md = json.dumps(self.metadata)
        lu = json.dumps(self.last_used, default=self.ordered_dict_to_dict)
        st = json.dumps(self.statistics)
        version = 2
        
        metadata_path = os.path.join(self.directory, f"(27399499ad89dce2b478e6d140b3a9d0)cache_metadata.json") # all the random bytes there are to avoid a collision with a item in the cache
        metadata = {
            "version": version,
            "cache_path_map": cpm,
            "metadata": md,
            "last_used": lu,
            "statistics": st
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=4)
    
    def __metadataLoad(self):
        """Internal function, loads metadata.
        """
        loadversion = 2
        
        metadata_path = os.path.join(self.directory, "(27399499ad89dce2b478e6d140b3a9d0)cache_metadata.json")
        if not os.path.exists(metadata_path):
            return False
        
        
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        except json.JSONDecodeError:
            
            self._print("metadata is not valid JSON", ErrorLevel.ERROR)
            self._print("metadata will be deleted, and cache will be wiped!", ErrorLevel.ERROR)
            os.remove(metadata_path)
            self.clear()
            return False
            
        if not "version" in metadata:
            self._print("metadata version not found", ErrorLevel.ERROR)
            return False
        elif metadata["version"] != loadversion:
            self._print("metadata version mismatch", ErrorLevel.ERROR)
            return False
        
        
        self.__cache_path_map = json.loads(metadata["cache_path_map"])
        self.metadata = json.loads(metadata["metadata"])
        self.last_used = json.loads(metadata["last_used"], object_pairs_hook=collections.OrderedDict)
        self.statistics = json.loads(metadata["statistics"])
    
    
    def put(self, key: str, value: Any, byte: bool, filext: Optional[str] = None, expiration: Optional[int] = None) -> str:
        """Put a value into the cache

        Args:
            key (str): They key used to refer to the item. The key *should not* contain a file extension. It will break things.
            Invalid chars: /, \, :, *, ?, ", <, >, |, ., and whitespace
            value (Any): The value stored. When passing in an item of type 'bytes', it will be written to disk using wb
            byte (bool): Override whether or not it's written with wb
            filext (Optional[str]): The file extension. Not including it will cause the file to have no ext.
            expiration (int): The point in time at which the file is no longer needed. It probably will remain on disc longer than then, but when
            trying to access it the next time, it will be deleted and return a cache miss, and will be deleted upon running the cleanup function if the time has expired.
            Note that not setting this value does not save your data from being deleted in a eviction pass.

        Returns:
            str: The key used to refer to the item.
        """
        estimated_size = len(value) if isinstance(value, (str, bytes)) else 0
        if self.statistics["size"] + estimated_size > self.max_size:
            self._print("cache full", ErrorLevel.WARNING)
            self.evict(EvictionMethod.LRU, 1)

        if any(c in key for c in ["\\", "/", ":", "*", "?", "\"", "<", ">", "|", " "]):
            raise ValueError("Invalid character in key")
        
        if filext == None:
            filext = ''
        if not filext.startswith('.') and not filext == '':
            filext = '.' + filext
        
        dictmode = False if not isinstance(value, dict) else True
        
            
        self.last_used[key] = time.time()
        self.metadata[key] = {"filext": filext, "expiration": expiration, "accessCount": 0, "bytes": byte, "dict": dictmode}
        self.__cache_path_map[key] = os.path.abspath(os.path.join(self.absdir, key + filext))
        
        if os.path.exists(self.__cache_path_map[key]):
            print("Warning: overwriting cache item at " + self.__cache_path_map[key])
            os.remove(self.__cache_path_map[key])
            
        with open(self.__cache_path_map[key], 'wb' if byte else 'w') as file:
            file.write(value if not dictmode else json.dumps(value))
        
        s = os.path.getsize(self.__cache_path_map[key])
        self.statistics["size"] += s
        
        self.metadata[key]["size"] = s
        
        self.statistics["saves"] += 1
        self.__metadataSave()
        
        return key
        
    
    def get(self, key: str) -> str | dict | bool:
        """Get a value from the cache

        Args:
            key (str): The key used to refer to the item. The key *should not* contain a file extension. It will break things.

        Returns:
            Any: The value stored. When passing in an item of type 'bytes', it will be written to disk using wb
        """
        if not key in self.__cache_path_map:
            self._print("cache miss: " + key, ErrorLevel.INFO)
            self.statistics["misses"] += 1
            return False
        elif not os.path.exists(self.__cache_path_map[key]): # if the key is in the cache, but it's not actually on disk
                self.delete(key)
                self._print(f"key {key} was orphaned (data was deleted but reference still exists)", ErrorLevel.WARNING)
                self._print("cache miss: " + key, ErrorLevel.INFO)
                self.statistics["misses"] += 1
                return False
    
        b = self.metadata[key].get("bytes", False)
        dictmode = self.metadata[key].get("dict", False)
        
        if self.metadata[key].get("expiration", -1):
            if time.time() > self.metadata[key].get("expiration", -1):
                self._print("cache miss: " + key + " expired", ErrorLevel.INFO)
                self.delete(key)
                return False
        
        self.last_used.move_to_end(key)
        value = self.__cache_path_map.get(key)
        self.statistics["hits"] += 1
        self.metadata[key]["accessCount"] += 1
        with open(value, 'r' if not b else 'rb') as file:
            value = file.read()
        
        self.last_used[key] = time.time()
        self.__metadataSave()
        
        return value if not dictmode else json.loads(value)

    
    def delete(self, key: str):
        """Delete a value from the cache

        Args:
            key (str): The key used to refer to the item. The key *should not* contain a file extension. It will break things.
        """
        with self.lock:
            if key in self.__cache_path_map:
                self.statistics["size"] -= self.metadata[key].get("size", 0)
                self.statistics["deletions"] += 1
                if os.path.exists(self.__cache_path_map[key]):
                    
                    try:
                        os.remove(self.__cache_path_map[key])
                    except (FileNotFoundError, PermissionError) as e:
                        self._print(f"Error removing cache item {key}: {e}", ErrorLevel.WARNING)
                try:
                    del self.__cache_path_map[key]
                    del self.metadata[key]
                    del self.last_used[key]
                    
                except KeyError as e:
                    self._print(f"KeyError encountered for key {key}: {e}", ErrorLevel.WARNING)
            else:
                self._print(f"key {key} not found", ErrorLevel.WARNING)
            
            self.__metadataSave()
    
    def clear(self):
        """Clear all values in the cache
        """
        for key in self.__cache_path_map:
            if os.path.exists(self.__cache_path_map[key]):
                    self.delete(key)
        self.__cache_path_map.clear()
        self.metadata.clear()
        self.last_used.clear()
        
        self.__metadataSave()
        
    def integrityCheck(self, restore: bool = False):
        """Runs collect and checks for cache integrity.
        """
        self._print("running cleanup", ErrorLevel.INFO)
       
        # use os.walk to check which keys are actually on disk
        for i in os.listdir(self.absdir):
            if not os.path.isfile(os.path.join(self.absdir, i)):
                continue
            
            if i == "(27399499ad89dce2b478e6d140b3a9d0)cache_metadata.json":
                continue
            
            i = i.split(os.path.extsep)[0]
            
            if not i in self.__cache_path_map:
                self._print(f"key {i} is orphaned (data is on disk but reference is missing)", ErrorLevel.WARNING)
                self.delete(i)
        
        for i in list(self.__cache_path_map.keys()):
            if not os.path.exists(self.__cache_path_map[i]):
                self._print(f"key {i} is orphaned (data was deleted but reference still exists)", ErrorLevel.WARNING)
                self.delete(i)
                continue
                
            data = self.getMetadata(i)
            if data.get("expiration", -1) == None: # this happens sometimes :/
                del self.metadata[i]["expiration"]
        
        self.collect()
        # self.__metadataSave() collect calls metadatasave for us!
        
    def collect(self):
        """Collect expired values from the cache
        """
        self._print("collecting expired items", ErrorLevel.INFO)
        self._print("collecting expired items", ErrorLevel.INFO)
        now = time.time()
        
        keys_to_delete = [key for key in list(self.metadata.keys()) if (-1 if self.metadata[key].get("expiration", 1.79e309) == None else self.metadata[key].get("expiration", 1.79e309)) < now]
    
        for key in keys_to_delete:
            self._print(f"deleting key {key} because it expired", ErrorLevel.INFO)
            self.delete(key)
    
        self.__metadataSave()
    
    def evict(self, method: EvictionMethod, amount: int):
        """Evict a certain amount of items from the cache

        Args:
            method (EvictionMethod): The method used to evict the items
            amount (int): The amount of items to evict
        """
        if method == EvictionMethod.LRU:
            for key in list(self.last_used.keys())[:amount]:
                self.statistics["evictions"] += 1
                self.delete(key)
        elif method == EvictionMethod.LFU:
            # sort by access count
            for key in sorted(self.metadata, key=lambda x: self.metadata[x]["accessCount"])[:amount]:
                self.statistics["evictions"] += 1
                self.delete(key)
        elif method == EvictionMethod.Largest:
            # sort by size
            for key in sorted(self.metadata, key=lambda x: self.metadata[x]["size"])[:amount]:
                self.statistics["evictions"] += 1
                self.delete(key)
        else:
            self._print("unknown eviction method", ErrorLevel.ERROR)
        
        self.__metadataSave()
    
    def getMetadata(self, key: str) -> dict:
        """Get the metadata of an item from the cache

        Args:
            key (str): The key used to refer to the item. The key *should not* contain a file extension. It will break things.

        Returns:
            dict: The metadata of the item
        """
        return self.metadata.get(key)

    def getKeyPath(self, key: str) -> str | bool:
        """Get the path of an item from the cache

        Args:
            key (str): The key used to refer to the item. The key *should not* contain a file extension. It will break things.

        Returns:
            str: The path of the item on disk
        """
        if not key in self.__cache_path_map:
            self._print("cache miss: " + key, ErrorLevel.INFO)
            self.statistics["misses"] += 1
            return False
        elif not os.path.exists(self.__cache_path_map[key]): # if the key is in the cache, but it's not actually on disk
                self.delete(key)
                self._print(f"key {key} was orphaned (data was deleted but reference still exists)", ErrorLevel.WARNING)
                self._print("cache miss: " + key, ErrorLevel.INFO)
                self.statistics["misses"] += 1
                return False
    
        b = self.metadata[key].get("bytes", False)
        dictmode = self.metadata[key].get("dict", False)
        
        if self.metadata[key].get("expiration", -1):
            if time.time() > self.metadata[key].get("expiration", -1):
                self._print("cache miss: " + key + " expired", ErrorLevel.INFO)
                self.delete(key)
                return False
        
        self.last_used.move_to_end(key)
        self.statistics["hits"] += 1
        self.last_used[key] = time.time()
        self.__metadataSave()
        return self.__cache_path_map.get(key)

    def getStatistics(self) -> dict:
        """Get the statistics of the cache

        Returns:
            dict: The statistics of the cache
        """
        return self.statistics

    def checkInCache(self, key: str) -> bool:
        """Check if an item is in the cache.
        # This function is only meant for 'checking' purposes. It does not take into account expiration or any other factors.
        If you're checking if you should call get() on the key, please call get() directly and check if it returns false.
        If you're checking if a key exists, you should call get() also, so it takes into account key expiration.
        In 70% of cases, what you need is get().

        Args:
            key (str): The key used to refer to the item. The key *should not* contain a file extension. It will break things.

        Returns:
            bool: Whether or not the item is in the cache
        """
        return key in self.__cache_path_map

    def _print(self, message: str, level: ErrorLevel):
        """Internal function, prints a message

        Args:
            message (str): The message to print
            level (ErrorLevel): The level of the message
        """
        print(f"cache {self.name} says: {message} | {level}") if level >= self.plevel else None