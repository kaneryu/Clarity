"""takes in a link, downloads the image, crops it to a square, rounds the corners, and returns the path to the image"""

from PIL import Image, ImageChops, ImageDraw
from src.cacheManager import getCache, ghash, CacheManager

from . import downloadimage, roundimage
import asyncio
from io import BytesIO

async def convertToCover(link: str, radius: int, size: int):
    """takes in a link, downloads the image, crops it to a square, rounds the corners, and returns the key to the image in the cache"""
    path = cache.getKeyPath(downloadimage.downloadimage(link, cache=cache))
    
    identifier = ghash(link + str(radius) + str(size))
    
    image = Image.open(path)
    width, height = image.size
    if width > height:
        image = image.crop((0, 0, height, height))
    elif height > width:
        image = image.crop((0, 0, width, width))
    
    # resize the image to the desired size
    image = image.resize((size, size), Image.LANCZOS)
    cache = getCache("images_cache")
    
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    image_bytes = buffer.getvalue()
    
    path = cache.getKeyPath(cache.put(ghash(identifier + "coverconverted"), image_bytes, byte=True, filext='.png', expiration=None))
    
    
    
    return await roundimage.roundimage(path, radius, cache=cache)


async def convertToCover_path(path: str, radius: int, size: int = -100, identify: str = ""):
    print("converting to cover, ", getCache("images_cache"))
    """takes in a path, crops it to a square, rounds the corners, and returns the key to the image in the cache"""
    identifier = ghash(path + str(radius) + str(size))
    image = Image.open(path)
    width, height = image.size
    if width > height:
        image = image.crop((0, 0, height, height))
    elif height > width:
        image = image.crop((0, 0, width, width))
    
    # resize the image to the desired size
    image = image.resize((size, size), Image.LANCZOS)
    
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    image_bytes = buffer.getvalue()
    
    cache = getCache("images_cache")
    print("cache is", cache)
    
    if identify:
        path = cache.getKeyPath(cache.put(ghash(identify), image_bytes, byte=True, filext='.png', expiration=None))
    else:
        path = cache.getKeyPath(cache.put(ghash(identifier + "coverconverted"), image_bytes, byte=True, filext='.png', expiration=None))
    
    
    
    return await roundimage.roundimage(path, radius, cache=cache)