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
        self.expiry_times = {}
        self.metadata = {}
        self.last_used = collections.OrderedDict()
        self.name = name or ""
        
        if directory == "":
            self.directory = f".{os.pathsep}{name}-cache" if not "cache" in name else f".{os.pathsep}{name}"
        else:
            self.directory = directory
            
        self.lock = asyncio.Lock()
        
        
        self.statistics = {
            "hits": 0,
            "misses": 0,
            "evictons": 0, # keeps track of how many items have been evicted
            "deletions": 0, # keeps track of how many items have been deleted, including evictions
            "size": 0
        }
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
        
        self.absdir = os.path.abspath(self.directory)
    
    
    def __metadataSave(self):
        """Internal function, saves metadata.
        """
        cpm = json.dumps(self.__cache_path_map)
        et = json.dumps(self.expiry_times)
        md = json.dumps(self.metadata)
        lu = json.dumps(self.last_used)
        
        metadata_path = os.path.join(self.directory, f"(27399499ad89dce2b478e6d140b3a9d0)cache_metadata.json") # all the random bytes there are to avoid a collision with a item in the cache
        metadata = {
            "cache_path_map": cpm,
            "expiry_times": et,
            "metadata": md,
            "last_used": lu
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=4)
    
    def __metadataLoad(self):
        """Internal function, loads metadata.
        """
        metadata_path = os.path.join(self.directory, "(27399499ad89dce2b478e6d140b3a9d0)cache_metadata.json")
        if not os.path.exists(metadata_path):
            return
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        self.__cache_path_map = json.loads(metadata["cache_path_map"])
        self.expiry_times = json.loads(metadata["expiry_times"])
        self.metadata = json.loads(metadata["metadata"])
        self.last_used = json.loads(metadata["last_used"])
    
    
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
        
            
        async with self.lock:
            
            self.last_used[key] = time.time()
            self.metadata[key] = {"filext": filext, "expiration": expiration, "accessCount": 0, "bytes": byte}
            self.__cache_path_map[key] = os.path.abspath(os.path.join(self.absdir, key + filext))
            with open(self.__cache_path_map[key], 'wb' if byte else 'w') as file:
                file.write(value)
            
            s = os.path.getsize(self.__cache_path_map[key])
            self.statistics["size"] += s
            self.metadata[key]["size"] = s
        
        self.__metadataSave()
        return key
        
    
    async def get(self, key: str) -> Any:
        """Get a value from the cache

        Args:
            key (str): The key used to refer to the item. The key *should not* contain a file extension. It will break things.

        Returns:
            Any: The value stored. When passing in an item of type 'bytes', it will be written to disk using wb
        """
        b = self.metadata[key].get("bytes", False)
        if not key in self.__cache_path_map:
            self._print("cache miss: " + key, ErrorLevel.INFO)
            self.statistics["misses"] += 1
            return None
        
        if key in self.expiry_times and time.time() > self.expiry_times[key]:
            self._print("cache miss: " + key + " expired", ErrorLevel.INFO)
            await self.delete(key)
            return None
        
        async with self.lock:
            self.last_used.move_to_end(key)
            value = self.__cache_path_map.get(key)
            self.statistics["hits"] += 1
            self.metadata[key]["accessCount"] += 1
            with open(value, 'r' if not b else 'rb') as file:
                value = file.read()
            
            self.last_used[key] = time.time()
            return value

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
                del self.expiry_times[key]
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
            self.expiry_times.clear()
            self.last_used.clear()
        
        self.__metadataSave()
    
    async def collect(self):
        """Collect expired values from the cache
        """
        async with self.lock:
            now = time.time()
            keys_to_delete = [key for key, expiry in self.expiry_times.items() if now > expiry]
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
    
    def scheckInCache(self, *args, **kwargs):
        """Check if an item is in the cache
        """
        return asyncio.run(self.checkInCache(*args, **kwargs))
    
    def _print(self, msg: str, level: ErrorLevel):
        print(f"cache[{self.name}] says {msg}, error level {str(level)}")