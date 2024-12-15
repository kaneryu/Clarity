from src.cacheManager import cacheManager as cacheManager_module
from hashlib import md5
import time

def ghash(thing):
    print("making hash for", thing, ":", md5(str(thing).encode()).hexdigest())
    return md5(str(thing).encode()).hexdigest()

globalCache = cacheManager_module.CacheManager(name="cache")
songCache = cacheManager_module.CacheManager(name="songs_cache")
imageCache = cacheManager_module.CacheManager(name="images_cache")