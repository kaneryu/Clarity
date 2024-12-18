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

import enum

class EvictionMethod(enum.StrEnum):
    LRU = "lru"
    LFU = "lfu"
    Largest = "largest"
    
class Btypes(enum.StrEnum):
    BYTES = 'b'
    TEXT = ''
    AUTO = 'a'

class ErrorLevel(enum.StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

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
        
        if directory == "":
            self.directory = f"{os.pathsep}{name}-cache" if not "cache" in name.lower() else f".{os.pathsep}{name}"
        else:
            self.directory = directory
            
        self.lock = asyncio.Lock()
        
        
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
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
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
    
    
    async def put(self, key: str, value: Any, byte: bool, filext: Optional[str] = None, expiration: Optional[int] = None) -> str:
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
            str: The path of the item on disk
        """
        estimated_size = len(value) if isinstance(value, (str, bytes)) else 0
        if self.statistics["size"] + estimated_size > self.max_size:
            self._print("cache full", ErrorLevel.WARNING)
            await self.evict(EvictionMethod.LRU, 1)

        if any(c in key for c in ["\\", "/", ":", "*", "?", "\"", "<", ">", "|", " "]):
            raise ValueError("Invalid character in key")
        
        if filext == None:
            filext = ''
        if not filext.startswith('.') and not filext == '':
            filext = '.' + filext
        
        dictmode = False if not isinstance(value, dict) else True
        
        async with self.lock:
            
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
        
    
    async def get(self, key: str) -> str | dict | bool:
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
    
        b = self.metadata[key].get("bytes", False)
        dictmode = self.metadata[key].get("dict", False)
        
        
        if time.time() > self.metadata[key].get("expiration", -1):
            self._print("cache miss: " + key + " expired", ErrorLevel.INFO)
            await self.delete(key)
            return False
        
        async with self.lock:
            self.last_used.move_to_end(key)
            value = self.__cache_path_map.get(key)
            self.statistics["hits"] += 1
            self.metadata[key]["accessCount"] += 1
            with open(value, 'r' if not b else 'rb') as file:
                value = file.read()
            
            self.last_used[key] = time.time()
            return value if not dictmode else json.loads(value)

        self.__metadataSave()
    
    async def delete(self, key: str):
        """Delete a value from the cache

        Args:
            key (str): The key used to refer to the item. The key *should not* contain a file extension. It will break things.
        """
        async with self.lock:
            if key in self.__cache_path_map:
                self.statistics["size"] -= self.metadata[key]["size"]
                self.statistics["deletions"] += 1
                os.remove(self.__cache_path_map[key])
                del self.__cache_path_map[key]
                del self.metadata[key]
                del self.last_used[key]
            else:
                self._print(f"key {key} not found", ErrorLevel.WARNING)
        
        self.__metadataSave()
    
    async def clear(self):
        """Clear all values in the cache
        """
        async with self.lock:
            for key in self.__cache_path_map:
                os.remove(self.__cache_path_map[key])
            self.__cache_path_map.clear()
            self.metadata.clear()
            self.last_used.clear()
        
        self.__metadataSave()
    
    async def collect(self):
        """Collect expired values from the cache
        """
        async with self.lock:
            now = time.time()
            
            keys_to_delete = [key for key in list(self.metadata.keys()) if self.metadata[key].get("expiration", -1) < now]
            for key in keys_to_delete:
                await self.delete(key)
        
        self.__metadataSave()
    
    async def evict(self, method: EvictionMethod, amount: int):
        """Evict a certain amount of items from the cache

        Args:
            method (EvictionMethod): The method used to evict the items
            amount (int): The amount of items to evict
        """
        async with self.lock:
            if method == EvictionMethod.LRU:
                for key in list(self.last_used.keys())[:amount]:
                    self.statistics["evictions"] += 1
                    await self.delete(key)
            elif method == EvictionMethod.LFU:
                # sort by access count
                for key in sorted(self.metadata, key=lambda x: self.metadata[x]["accessCount"])[:amount]:
                    self.statistics["evictions"] += 1
                    await self.delete(key)
            elif method == EvictionMethod.Largest:
                # sort by size
                for key in sorted(self.metadata, key=lambda x: self.metadata[x]["size"])[:amount]:
                    self.statistics["evictions"] += 1
                    await self.delete(key)
            else:
                self._print("unknown eviction method", ErrorLevel.ERROR)
        
        self.__metadataSave()
    
    async def getMetadata(self, key: str) -> dict:
        """Get the metadata of an item from the cache

        Args:
            key (str): The key used to refer to the item. The key *should not* contain a file extension. It will break things.

        Returns:
            dict: The metadata of the item
        """
        return self.metadata.get(key)

    async def getKeyPath(self, key: str) -> str:
        """Get the path of an item from the cache

        Args:
            key (str): The key used to refer to the item. The key *should not* contain a file extension. It will break things.

        Returns:
            str: The path of the item on disk
        """
        return self.__cache_path_map.get(key)

    async def getStatistics(self) -> dict:
        """Get the statistics of the cache

        Returns:
            dict: The statistics of the cache
        """
        return self.statistics

    async def checkInCache(self, key: str) -> bool:
        """Check if an item is in the cache

        Args:
            key (str): The key used to refer to the item. The key *should not* contain a file extension. It will break things.

        Returns:
            bool: Whether or not the item is in the cache
        """
        return key in self.__cache_path_map

    def sput(self, *args, **kwargs):
        """Put a value into the cache
        """
        return asyncio.run(self.put(*args, **kwargs))
    
    def sget(self, *args, **kwargs):
        """Get a value from the cache
        """
        return asyncio.run(self.get(*args, **kwargs))
    
    def sdelete(self, *args, **kwargs):
        """Delete a value from the cache
        """
        return asyncio.run(self.delete(*args, **kwargs))
    
    def sclear(self, *args, **kwargs):
        """Clear all values in the cache
        """
        return asyncio.run(self.clear(*args, **kwargs))
    
    def scollect(self, *args, **kwargs):
        """Collect expired values from the cache
        """
        return asyncio.run(self.collect(*args, **kwargs))
    
    def sevict(self, *args, **kwargs):
        """Evict a certain amount of items from the cache
        """
        return asyncio.run(self.evict(*args, **kwargs))
    
    def sgetMetadata(self, *args, **kwargs):
        """Get the metadata of an item from the cache
        """
        return asyncio.run(self.getMetadata(*args, **kwargs))
    
    def sgetKeyPath(self, *args, **kwargs):
        """Get the path of an item from the cache
        """
        return asyncio.run(self.getKeyPath(*args, **kwargs))
    
    def sgetStatistics(self, *args, **kwargs):
        """Get the statistics of the cache
        """
        return asyncio.run(self.getStatistics(*args, **kwargs))
    
    def scheckInCache(self, key: str) -> bool:
        """Check if an item is in the cache
        """
        return asyncio.run(self.checkInCache(key))
    
    def _print(self, msg: str, level: ErrorLevel):
        print(f"cache[{self.name}] says {msg}, error level {str(level)}")