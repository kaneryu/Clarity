from PIL import Image, ImageChops, ImageDraw
from src.cacheManager import getCache, ghash, CacheManager
import asyncio
from io import BytesIO


imageCache = getCache("images_cache")
async def roundimage(image: str, radius = 20, cache: CacheManager = imageCache) -> int:
    """rounds an image from local path, and returns key of the image in cache
    """
    hsh = ghash(image + "rounded" + str(radius))
    if cache.checkInCache(hsh): # check if the rounded image is cached
        return cache.getKeyPath(hsh) # return the path of the image
    
    im: Image.Image = Image.open(image).convert('RGBA')
    bigsize = (im.size[0] * 3, im.size[1] * 3) # define the size of the mask as 3x the size of the image
    mask = Image.new('L', bigsize, 0) # create a black mask
    ImageDraw.Draw(mask).rounded_rectangle(xy=(0, 0, bigsize[0], bigsize[1]), radius=radius, fill=255) # draw a white sqircle in the mask
    mask = mask.resize(im.size, resample=Image.LANCZOS) # resize the mask to the size of the image, and antialiasing it down
    mask = ImageChops.darker(mask, im.split()[-1]) # use the alpha channel of the image as a mask
    im.putalpha(mask) # put the mask into the alpha channel of the image
    
    buffer = BytesIO()
    im.save(buffer, format='PNG')
    image_bytes = buffer.getvalue()
    
    key = cache.put(ghash(image + "rounded" + str(radius)), image_bytes, byte=True, filext='.png', expiration=None)
    
    return key

