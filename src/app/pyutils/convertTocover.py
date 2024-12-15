"""takes in a link, downloads the image, crops it to a square, rounds the corners, and returns the path to the image"""

from PIL import Image, ImageChops, ImageDraw
from src.globals import imageCache, ghash
from src.cacheManager import CacheManager

from . import downloadimage, roundimage
import asyncio
from io import BytesIO

async def convertToCover(link: str, radius: str, size: int, *, cache: CacheManager = imageCache):
    """takes in a link, downloads the image, crops it to a square, rounds the corners, and returns the key to the image in the cache"""

    path = await cache.getKeyPath(await downloadimage.downloadimage(link, cache=cache))
    
    
    
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
    
    path = await cache.getKeyPath(await cache.put(ghash(link + "coverconverted"), image_bytes, byte=True, filext='.png', expiration=None))
    
    
    
    return await roundimage.roundimage(path, radius, cache=cache)