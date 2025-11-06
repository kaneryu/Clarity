"""Global data store for the application.
Quite similar to the cacheManager module, but this one is more persistent and is used for storing data that is not meant to be evicted.
"""

import time
from typing import Any, Optional, Union, cast as typing_cast, Literal
import os
import json
import collections
from hashlib import md5
from dataclasses import dataclass, asdict

import io
import logging


def ghash(thing):
    # print("making hash for", thing, ":", md5(str(thing).encode()).hexdigest())
    return md5(str(thing).encode()).hexdigest()


def dataStoreExists(name: str) -> bool:
    """Check if a dataStore exists

    Args:
        name (str): The name of the dataStore

    Returns:
        bool: Whether or not the dataStore exists
    """
    return name in dataStores


def getdataStore(name: str) -> "DataStore":
    """Get a dataStore by name, creating it if it does not exist.

    Args:
        name (str): The name of the dataStore

    Returns:
        DataStore: The dataStore
    """
    return dataStores[name] if name in dataStores else DataStore(name)


@dataclass
class DataStoreStatistics:
    hits: int = 0
    misses: int = 0
    saves: int = 0
    evictons: int = 0
    deletions: int = 0
    size: int = 0


class DataStore:
    def __init__(self, name: str, directory: str = ""):
        """Initialize the DataStore.
        Note that this dataStore is long-term persistent only
        Args:
            directory (str): Directory to store persistent dataStore files.
            name (str): Name for the dataStore.
        """
        self.max_size = 1000000000  # 1GB
        self.__dataStore_path_map: dict[str, str] = {}
        self.metadata: dict[str, dict] = {}
        self.last_used: collections.OrderedDict = collections.OrderedDict()
        self.name = name or ""

        if directory == "":
            self.directory = (
                f".{os.pathsep}{name}-dataStore"
                if not "datatore" in name.lower()
                else f".{os.pathsep}{name}"
            )
        else:
            self.directory = directory

        self.statistics = DataStoreStatistics()
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)

        self.absdir = os.path.abspath(self.directory)

        dataStores[name] = self

        self.logging = logging.getLogger(f"{name}-dataStore")

        if not self.__metadataLoad():
            self.__metadataSave()

    def ordered_dict_to_dict(self, obj):
        if isinstance(obj, collections.OrderedDict):
            return dict(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    def __metadataSave(self):
        """Internal function, saves metadata."""
        cpm = json.dumps(self.__dataStore_path_map)
        md = json.dumps(self.metadata)
        lu = json.dumps(self.last_used, default=self.ordered_dict_to_dict)
        st = json.dumps(asdict(self.statistics))
        version = 2

        metadata_path = os.path.join(
            self.directory, f"(27399499ad89dce2b478e6d140b3a9d0)dataStore_metadata.json"
        )  # all the random bytes there are to avoid a collision with a item in the dataStore
        metadata = {
            "version": version,
            "dataStore_path_map": cpm,
            "metadata": md,
            "last_used": lu,
            "statistics": st,
        }

        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=4)

    def __metadataLoad(self):
        """Internal function, loads metadata."""
        loadversion = 2

        metadata_path = os.path.join(
            self.directory, "(27399499ad89dce2b478e6d140b3a9d0)dataStore_metadata.json"
        )
        if not os.path.exists(metadata_path):
            return False

        with open(metadata_path, "r") as f:
            try:
                metadata = json.load(f)
            except json.JSONDecodeError:
                self.logging.error("metadata file corrupted")
                self.last_used = collections.OrderedDict()
                self.statistics = DataStoreStatistics()
                self.metadata = {}
                self.integrityCheck(restore=True)
                return False

        if not "version" in metadata:
            self.logging.error("metadata version not found")
            return False
        elif metadata["version"] != loadversion:
            self.logging.error("metadata version mismatch")
            return False

        self.__dataStore_path_map = json.loads(metadata["dataStore_path_map"])
        self.metadata = json.loads(metadata["metadata"])
        self.last_used = json.loads(
            metadata["last_used"], object_pairs_hook=collections.OrderedDict
        )
        self.statistics = DataStoreStatistics(**json.loads(metadata["statistics"]))

    def __wfsetup(
        self,
        key: str,
        value: str | bytes | dict | io.BytesIO,
        byte: bool = False,
        ext: Optional[str] = None,
    ):

        estimated_size = len(value) if isinstance(value, (str, bytes)) else 0
        if self.statistics.size + estimated_size > self.max_size:
            self.logging.warning("dataStore full")

        if any(c in key for c in ["\\", "/", ":", "*", "?", '"', "<", ">", "|", " "]):
            raise ValueError("Invalid character in key")

        if ext == None:
            ext = ""
        if not ext.startswith(".") and not ext == "":
            ext = "." + ext

        if isinstance(value, io.BytesIO):
            value = value.getvalue()
            byte = True

        self.__dataStore_path_map[key] = os.path.abspath(
            os.path.join(self.absdir, key + ext)
        )

        if os.path.exists(self.__dataStore_path_map[key]):
            self.logging.error(f"key {key} already exists")
            return False

        return (byte, ext)

    def __wfexit(self, key: str, byte: bool, ext: str, dictmode: bool):

        s = os.path.getsize(self.__dataStore_path_map[key])
        self.last_used[key] = time.time()
        self.metadata[key] = {
            "ext": ext,
            "accessCount": 0,
            "bytes": byte,
            "dict": dictmode,
        }
        self.statistics.size += s
        self.metadata[key]["size"] = s
        self.statistics.saves += 1
        self.__metadataSave()

    def write_file(
        self,
        key: str,
        value: str | bytes | dict | io.BytesIO,
        byte: bool = False,
        ext: Optional[str] = None,
    ) -> str | bool:
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

        with open(self.__dataStore_path_map[key], "wb" if byte else "w") as file:
            file.write(value if not dictmode else json.dumps(value))

        self.__wfexit(key, byte, ext, dictmode)

        return key

    def open_write_file(
        self,
        key: str,
        bytes: bool,
        ext: Optional[str] = None,
        allowappend: Optional[bool] = False,
    ) -> io.FileIO:
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
                return typing_cast(
                    io.FileIO,
                    open(self.__dataStore_path_map[key], "ab" if bytes else "a"),
                )
            else:
                return typing_cast(
                    io.FileIO,
                    open(self.__dataStore_path_map[key], "wb" if bytes else "w"),
                )
        else:
            return typing_cast(
                io.FileIO, open(self.__dataStore_path_map[key], "wb" if bytes else "w")
            )

    def close_write_file(self, key: str, ext: str, file: io.FileIO):
        """Close a file opened with open_write_file

        Args:
            key (str): key / filename
            file (io.FileIO): the file object
        """

        file.close()

        self.__wfexit(key, True if "b" in file.mode else False, ext, False)

    def get_file(self, key: str) -> Any:
        """Get a file from the dataStore

        Args:
            key (str): The key used to refer to the item. The key *should not* contain a file extension. It will break things.

        Returns:
            Any: The value stored. When passing in an item of type 'bytes', it will be written to disk using wb
        """
        if not key in self.__dataStore_path_map:
            self.logging.debug("dataStore miss: " + key)
            self.statistics.misses += 1
            return False
        elif not os.path.exists(
            self.__dataStore_path_map[key]
        ):  # if the key is in the dataStore, but it's not actually on disk
            self.delete(key)
            self.logging.warning(
                f"key {key} was orphaned (data was deleted but reference still exists)"
            )
            self.logging.debug("dataStore miss: " + key)
            self.statistics.misses += 1
            return False

        b = self.metadata[key].get("bytes", False)
        dictmode = self.metadata[key].get("dict", False)

        self.last_used.move_to_end(key)
        value = self.__dataStore_path_map[key]
        self.statistics.hits += 1
        self.metadata[key]["accessCount"] += 1
        with open(value, "r" if not b else "rb") as file:
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
            try:
                self.statistics.size -= self.metadata[key]["size"]
                self.statistics.deletions += 1
                if os.path.exists(self.__dataStore_path_map[key]):
                    os.remove(self.__dataStore_path_map[key])
                del self.__dataStore_path_map[key]
                del self.metadata[key]
                del self.last_used[key]
            except KeyError:
                pass
        else:
            self.logging.warning(f"key {key} not found")

        self.__metadataSave()

    def clear(self):
        """Clear all files in the dataStore"""
        for key in self.__dataStore_path_map:
            if os.path.exists(self.__dataStore_path_map[key]):
                os.remove(self.__dataStore_path_map[key])
        self.__dataStore_path_map.clear()
        self.metadata.clear()
        self.last_used.clear()

        self.__metadataSave()

    def integrityCheck(self, restore: bool = False):
        """Runs collect and checks for dataStore integrity."""
        if not restore:
            return

        meta_filename = "(27399499ad89dce2b478e6d140b3a9d0)dataStore_metadata.json"
        restored_any = False

        try:
            for entry in os.listdir(self.directory):
                path = os.path.join(self.directory, entry)
                if not os.path.isfile(path):
                    continue
                if entry == meta_filename:
                    continue

                root, ext = os.path.splitext(entry)
                key = root
                abs_path = os.path.abspath(path)
                size_on_disk = os.path.getsize(path)

                # Ensure path map
                if key not in self.__dataStore_path_map:
                    self.__dataStore_path_map[key] = abs_path
                    # Minimal, safe defaults for restored files
                    self.metadata[key] = {
                        "ext": ext,
                        "accessCount": 0,
                        "bytes": True,  # default to binary for safety
                        "dict": False,
                        "size": size_on_disk,
                    }
                    self.statistics.size += size_on_disk
                    restored_any = True
                else:
                    # Sync path and metadata details
                    self.__dataStore_path_map[key] = abs_path
                    md = self.metadata.get(key, {})

                    prev_size = md.get("size", 0)
                    if prev_size != size_on_disk:
                        self.statistics.size += size_on_disk - prev_size
                        md["size"] = size_on_disk
                        restored_any = True

                    if md.get("ext") != ext:
                        md["ext"] = ext
                        restored_any = True

                    if "bytes" not in md:
                        md["bytes"] = True
                        restored_any = True

                    if "dict" not in md:
                        md["dict"] = False
                        restored_any = True

                    if "accessCount" not in md:
                        md["accessCount"] = 0
                        restored_any = True

                    self.metadata[key] = md

                # Ensure last_used entry exists
                if key not in self.last_used:
                    try:
                        ts = os.path.getmtime(path)
                    except Exception:
                        ts = time.time()
                    self.last_used[key] = ts
                    restored_any = True
        except Exception:
            self.logging.exception("integrityCheck restore failed")
        finally:
            if restored_any:
                self.__metadataSave()

    def getMetadata(self, key: str) -> dict | None:
        """Get the metadata of an item from the dataStore

        Args:
            key (str): The key used to refer to the item. The key *should not* contain a file extension. It will break things.

        Returns:
            dict: The metadata of the item
        """
        return self.metadata.get(key)

    def getFilePath(self, key: str) -> str | Literal[False]:
        """Get the path of an file from the dataStore

        Args:
            key (str): The key used to refer to the file. The key *should not* contain a file extension. It will break things.

        Returns:
            str: The path of the file on disk
        """

        if not key in self.__dataStore_path_map:
            self.logging.debug("dataStore miss: " + key)
            self.statistics.misses += 1
            return False
        elif not os.path.exists(
            self.__dataStore_path_map[key]
        ):  # if the key is in the dataStore, but it's not actually on disk
            self.delete(key)
            self.logging.warning(
                f"key {key} was orphaned (data was deleted but reference still exists)"
            )
            self.logging.debug("dataStore miss: " + key)
            self.statistics.misses += 1
            return False
        try:
            self.last_used.move_to_end(key)
        except KeyError:
            self.last_used[key] = time.time()

        self.statistics.hits += 1
        self.last_used[key] = time.time()
        self.__metadataSave()

        return self.__dataStore_path_map[key]

    def getStatistics(self) -> dict:
        """Get the statistics of the dataStore

        Returns:
            dict: The statistics of the dataStore
        """
        return asdict(self.statistics)

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


dataStores: dict[str, DataStore] = {}
