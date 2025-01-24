"""Global data store for the application.
    Quite similar to the cacheManager module, but this one is more persistent and is used for storing data that is not meant to be evicted.
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

import io

def ghash(thing):
    # print("making hash for", thing, ":", md5(str(thing).encode()).hexdigest())
    return md5(str(thing).encode()).hexdigest()

    
class Btypes(enum.StrEnum):
    BYTES = 'b'
    TEXT = ''
    AUTO = 'a'

class ErrorLevel(enum.StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

dataStores = {}

def dataStoreExists(name: str) -> bool:
    """Check if a dataStore exists

    Args:
        name (str): The name of the dataStore

    Returns:
        bool: Whether or not the dataStore exists
    """
    return name in dataStores

def getdataStore(name: str) -> "DataStore":
    """Get a dataStore by name

    Args:
        name (str): The name of the dataStore

    Returns:
        DataStore: The dataStore
    """
    return dataStores.get(name)

    
class DataStore:
    def __init__(self, name: str, directory: str = ""):
        """Initialize the DataStore.
        Note that this dataStore is long-term persistent only
        Args:
            directory (str): Directory to store persistent dataStore files.
            name (str): Name for the dataStore.
        """
        self.max_size = 1000000000 # 1GB
        self.__dataStore_path_map = {}
        self.metadata: dict[str, dict] = {}
        self.last_used = collections.OrderedDict()
        self.name = name or ""
        
        if directory == "":
            self.directory = f".{os.pathsep}{name}-dataStore" if not "datatore" in name.lower() else f".{os.pathsep}{name}"
        else:
            self.directory = directory
            
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
        
        dataStores[name] = self
        
        if not self.__metadataLoad():
            self.__metadataSave()
            
    def ordered_dict_to_dict(self, obj):
        if isinstance(obj, collections.OrderedDict):
            return dict(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    def __metadataSave(self):
        """Internal function, saves metadata.
        """
        cpm = json.dumps(self.__dataStore_path_map)
        md = json.dumps(self.metadata)
        lu = json.dumps(self.last_used, default=self.ordered_dict_to_dict)
        st = json.dumps(self.statistics)
        version = 2
        
        metadata_path = os.path.join(self.directory, f"(27399499ad89dce2b478e6d140b3a9d0)dataStore_metadata.json") # all the random bytes there are to avoid a collision with a item in the dataStore
        metadata = {
            "version": version,
            "dataStore_path_map": cpm,
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
        
        metadata_path = os.path.join(self.directory, "(27399499ad89dce2b478e6d140b3a9d0)dataStore_metadata.json")
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
        
        
        self.__dataStore_path_map = json.loads(metadata["dataStore_path_map"])
        self.metadata = json.loads(metadata["metadata"])
        self.last_used = json.loads(metadata["last_used"], object_pairs_hook=collections.OrderedDict)
        self.statistics = json.loads(metadata["statistics"])
    
               
    def __wfsetup(self, key: str, value: str | bytes | dict | io.BytesIO, byte: bool = False, ext: Optional[str] = None):
        
        estimated_size = len(value) if isinstance(value, (str, bytes)) else 0
        if self.statistics["size"] + estimated_size > self.max_size:
            self._print("dataStore full", ErrorLevel.WARNING)

        if any(c in key for c in ["\\", "/", ":", "*", "?", "\"", "<", ">", "|", " "]):
            raise ValueError("Invalid character in key")
        
        if ext == None:
            ext = ''
        if not ext.startswith('.') and not ext == '':
            ext = '.' + ext
        
        if isinstance(value, io.BytesIO):
            value = value.getvalue()
            byte = True
        
        self.__dataStore_path_map[key] = os.path.abspath(os.path.join(self.absdir, key + ext))
        
        if os.path.exists(self.__dataStore_path_map[key]):
            self._print(f"key {key} already exists", ErrorLevel.ERROR)
            return False

        return (byte, ext)
    
    def __wfexit(self, key: str, byte: bool, ext: str, dictmode: bool):

        s = os.path.getsize(self.__dataStore_path_map[key])
        self.last_used[key] = time.time()
        self.metadata[key] = {"ext": ext, "accessCount": 0, "bytes": byte, "dict": dictmode}
        self.statistics["size"] += s
        self.metadata[key]["size"] = s
        self.statistics["saves"] += 1
        self.__metadataSave()
        
    def write_file(self, key: str, value: str | bytes | dict | io.BytesIO, byte: bool = False, ext: Optional[str] = None) -> str:
        """write a file into the dataStore

        Args:
            key (str): They key used to refer to the item. The key *should not* contain a file extension. It will break things.
            Invalid chars: /, \\, :, *, ?, ", <, >, |, ., and whitespace
            value (Any): The value stored. When passing in an item of type 'bytes', it will be written to disk using wb
            byte (bool): Override whether or not it's written with wb
            ext (Optional[str]): The file extension. Not including it will cause the file to have no ext.

        Returns:
            str: The key used to refer to the item.
        """
        dictmode = False if not isinstance(value, dict) else True
        byte = byte or isinstance(value, bytes)

        setres = self.__wfsetup(key, value, byte, ext)
        if setres == False:
            return False
        
        byte, ext = setres
        
        with open(self.__dataStore_path_map[key], 'wb' if byte else 'w') as file:
            file.write(value if not dictmode else json.dumps(value))

        self.__wfexit(key, byte, ext, dictmode)
        
        return key
    
    def open_write_file(self, key: str, bytes: bool, ext: Optional[str] = None, allowappend: Optional[bool] = False) -> io.FileIO:
        """Open a file for writing in the datastore, returns a file object
        Close the file with close_write_file, not by calling close on the file object

        Args:
            key (str): key / filename
            ext (Optional[str], optional): file ext. Defaults to None.

        Returns:
            io.FileIO: the file object, 
        """
        self.__wfsetup(key, "", False, ext)
        if allowappend:
            if os.path.exists(self.__dataStore_path_map[key]):
                return open(self.__dataStore_path_map[key], 'ab' if bytes else 'a')
            else:
                return open(self.__dataStore_path_map[key], 'wb' if bytes else 'w')
        else:
            return open(self.__dataStore_path_map[key], 'wb' if bytes else 'w')

    def close_write_file(self, key: str, ext: str, file: io.FileIO):
        """Close a file opened with open_write_file

        Args:
            key (str): key / filename
            file (io.FileIO): the file object
        """
        
        file.close()
        
        self.__wfexit(key, True if 'b' in file.mode else False, ext, False)
    
    def get_file(self, key: str) -> str | dict | bool:
        """Get a file from the dataStore

        Args:
            key (str): The key used to refer to the item. The key *should not* contain a file extension. It will break things.

        Returns:
            Any: The value stored. When passing in an item of type 'bytes', it will be written to disk using wb
        """
        if not key in self.__dataStore_path_map:
            self._print("dataStore miss: " + key, ErrorLevel.INFO)
            self.statistics["misses"] += 1
            return False
        elif not os.path.exists(self.__dataStore_path_map[key]): # if the key is in the dataStore, but it's not actually on disk
                self.delete(key)
                self._print(f"key {key} was orphaned (data was deleted but reference still exists)", ErrorLevel.WARNING)
                self._print("dataStore miss: " + key, ErrorLevel.INFO)
                self.statistics["misses"] += 1
                return False
    
        b = self.metadata[key].get("bytes", False)
        dictmode = self.metadata[key].get("dict", False)
        
        self.last_used.move_to_end(key)
        value = self.__dataStore_path_map.get(key)
        self.statistics["hits"] += 1
        self.metadata[key]["accessCount"] += 1
        with open(value, 'r' if not b else 'rb') as file:
            value = file.read()
        
        self.last_used[key] = time.time()
        self.__metadataSave()
        
        return value if not dictmode else json.loads(value)

    
    def delete(self, key: str):
        """Delete a value from the dataStore

        Args:
            key (str): The key used to refer to the item. The key *should not* contain a file extension. It will break things.
        """
        if key in self.__dataStore_path_map:
            self.statistics["size"] -= self.metadata[key]["size"]
            self.statistics["deletions"] += 1
            if os.path.exists(self.__dataStore_path_map[key]):
                    os.remove(self.__dataStore_path_map[key])
            del self.__dataStore_path_map[key]
            del self.metadata[key]
            del self.last_used[key]
        else:
            self._print(f"key {key} not found", ErrorLevel.WARNING)
        
        self.__metadataSave()
    
    def clear(self):
        """Clear all files in the dataStore
        """
        for key in self.__dataStore_path_map:
            if os.path.exists(self.__dataStore_path_map[key]):
                    os.remove(self.__dataStore_path_map[key])
        self.__dataStore_path_map.clear()
        self.metadata.clear()
        self.last_used.clear()
        
        self.__metadataSave()
        
    def integrityCheck(self, restore: bool = False):
        """Runs collect and checks for dataStore integrity.
        """
        self._print("running cleanup", ErrorLevel.INFO)
       
        # use os.listdir to check which keys are actually on disk
        for i in os.listdir(self.absdir):
            if not os.path.isfile(os.path.join(self.absdir, i)):
                continue
            
            if i == "(27399499ad89dce2b478e6d140b3a9d0)dataStore_metadata.json":
                continue
            
            i = i.split(os.path.extsep)[0]
            
            if not i in self.__dataStore_path_map:
                self._print(f"key {i} is orphaned (data is on disk but reference is missing)", ErrorLevel.WARNING)
                if restore:
                    self._print(f"key {i} will be restored", ErrorLevel.INFO)
                    data = open(os.path.join(self.absdir, i), 'r').read()
                    os.remove(os.path.join(self.absdir, i))
                    self.put(i, data, Btypes.AUTO, expiration=None)
                else:
                    self._print(f"key {i} will be not be restored", ErrorLevel.INFO)
        
        for i in self.__dataStore_path_map:
            if not os.path.exists(self.__dataStore_path_map[i]):
                self._print(f"key {i} is orphaned (data was deleted but reference still exists)", ErrorLevel.WARNING)
                self.delete(i)
                continue
                
            data = self.getMetadata(i)
            if data.get("expiration", -1) == None: # this happens sometimes :/
                del self.metadata[i]["expiration"]
                
        self.__metadataSave()
    
    def getMetadata(self, key: str) -> dict:
        """Get the metadata of an item from the dataStore

        Args:
            key (str): The key used to refer to the item. The key *should not* contain a file extension. It will break things.

        Returns:
            dict: The metadata of the item
        """
        return self.metadata.get(key)

    def getFilePath(self, key: str) -> str | bool:
        """Get the path of an file from the dataStore

        Args:
            key (str): The key used to refer to the file. The key *should not* contain a file extension. It will break things.

        Returns:
            str: The path of the file on disk
        """
        
        print(self.__dataStore_path_map[key])
        
        if not key in self.__dataStore_path_map:
            self._print("dataStore miss: " + key, ErrorLevel.INFO)
            self.statistics["misses"] += 1
            return False
        elif not os.path.exists(self.__dataStore_path_map[key]): # if the key is in the dataStore, but it's not actually on disk
                self.delete(key)
                self._print(f"key {key} was orphaned (data was deleted but reference still exists)", ErrorLevel.WARNING)
                self._print("dataStore miss: " + key, ErrorLevel.INFO)
                self.statistics["misses"] += 1
                return False
        
        self.last_used.move_to_end(key)
        self.statistics["hits"] += 1
        self.last_used[key] = time.time()
        self.__metadataSave()
        
        return self.__dataStore_path_map.get(key)

    def getStatistics(self) -> dict:
        """Get the statistics of the dataStore

        Returns:
            dict: The statistics of the dataStore
        """
        return self.statistics

    def checkFileExists(self, key: str) -> bool:
        """Check if an item is in the dataStore.

        Args:
            key (str): The key used to refer to the item. The key *should not* contain a file extension. It will break things.

        Returns:
            bool: Whether or not the item is in the dataStore
        """
        p = self.__dataStore_path_map.get(key)
        if not p:
            return False
        return os.path.exists(p)

    def getAll(self) -> dict:
        """Get all items in the dataStore

        Returns:
            dict: All items in the dataStore
        """
        return self.__dataStore_path_map

    def _print(self, message: str, level: ErrorLevel):
        """Internal function, prints a message

        Args:
            message (str): The message to print
            level (ErrorLevel): The level of the message
        """
        print(f"dataStore {self.name} says: {message} | {level}")