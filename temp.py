import src.cacheManager as cacheManager_module
import asyncio

c = cacheManager_module.CacheManager(name="images_cache")

async def main():
    await c.integrityCheck()

asyncio.run(main())