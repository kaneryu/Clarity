from src.cacheManager import getCache, ghash, CacheManager
from src.network import networkManager
import asyncio
import requests
from typing import Optional

"""downloads an image from the internet, checking the cache first"""


imageCache = getCache("images_cache")
async def downloadimage(url: str, cache: CacheManager = imageCache) -> str:
    """downloads an image from the internet, checking the cache, and returns key of the image in the cache
    """
    hsh = ghash(url)
    if not cache.checkInCache(hsh): # if the image is not in the cache
        r = networkManager.get(url)
        cache.put(hsh, r.content, filext = ".png", byte = True)
    
    return hsh