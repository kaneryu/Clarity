"""takes in a link, downloads the image, crops it to a square, rounds the corners, and returns the path to the image"""

from PIL import Image, ImageChops, ImageDraw
from src.cacheManager import getCache, ghash, CacheManager

from . import downloadimage, roundimage
import asyncio
from io import BytesIO

imageCache = getCache("images_cache")

async def convertToCover(link: str, radius: str, size: int, *, cache: CacheManager = imageCache):
    """takes in a link, downloads the image, crops it to a square, rounds the corners, and returns the key to the image in the cache"""

    path = cache.getKeyPath(downloadimage.downloadimage(link, cache=cache))
    
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
    
    path = cache.getKeyPath(cache.put(ghash(link + "coverconverted"), image_bytes, byte=True, filext='.png', expiration=None))
    
    
    
    return await roundimage.roundimage(path, radius, cache=cache)


async def convertToCover_path(path: str, radius: int, size: int = -100, identify: str = "", *, cache: CacheManager = imageCache):
    """takes in a path, downloads the image, crops it to a square, rounds the corners, and returns the key to the image in the cache"""
    
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
    
    if identify:
        path = cache.getKeyPath(cache.put(ghash(identify), image_bytes, byte=True, filext='.png', expiration=None))
    else:
        path = cache.getKeyPath(cache.put(ghash(path + "coverconverted"), image_bytes, byte=True, filext='.png', expiration=None))
    
    
    
    return await roundimage.roundimage(path, radius, cache=cache)