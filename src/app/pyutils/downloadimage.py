from src.globals import imageCache, ghash
from src.cacheManager import CacheManager
import asyncio
import requests
from typing import Optional

"""downloads an image from the internet, checking the cache first"""



async def downloadimage(url: str, cache: Optional[CacheManager] = imageCache) -> str:
    """downloads an image from the internet, checking the cache, and returns key of the image in the cache
    """
    hsh = ghash(url)
    if not await cache.checkInCache(hsh): # if the image is not in the cache
        r = requests.get(url)
        await cache.put(hsh, r.content, filext = ".png", byte = True)
    
    return hsh