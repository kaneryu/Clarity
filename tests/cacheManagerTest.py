import unittest
import asyncio
import os
from src.cacheManager.cacheManager import CacheManager

class TestCacheManager(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.get_event_loop()
        self.cache_dir = "test_cache"
        self.cache_manager = CacheManager(self.cache_dir)

    def tearDown(self):
        if os.path.exists(self.cache_dir):
            for file in os.listdir(self.cache_dir):
                os.remove(os.path.join(self.cache_dir, file))
            os.rmdir(self.cache_dir)

    def test_put_and_get(self):
        async def run_test():
            await self.cache_manager.put("key1", "value1")
            value = await self.cache_manager.get("key1")
            self.assertEqual(value, "value1")

        self.loop.run_until_complete(run_test())

    def test_put_with_expiry(self):
        async def run_test():
            await self.cache_manager.put("key2", "value2", expires_in=1)
            # await asyncio.sleep(2)
            value = await self.cache_manager.get("key2")
            self.assertIsNone(value)

        self.loop.run_until_complete(run_test())

    def test_put_persistent(self):
        async def run_test():
            await self.cache_manager.put("key3", "value3", persistent=True)
            value = self.cache_manager._load_from_disk("key3")
            self.assertEqual(value, "value3")

        self.loop.run_until_complete(run_test())

    def test_delete(self):
        async def run_test():
            await self.cache_manager.put("key4", "value4")
            await self.cache_manager.delete("key4")
            value = await self.cache_manager.get("key4")
            self.assertIsNone(value)

        self.loop.run_until_complete(run_test())

    def test_clear(self):
        async def run_test():
            await self.cache_manager.put("key5", "value5")
            await self.cache_manager.put("key6", "value6")
            await self.cache_manager.clear()
            value1 = await self.cache_manager.get("key5")
            value2 = await self.cache_manager.get("key6")
            self.assertIsNone(value1)
            self.assertIsNone(value2)

        self.loop.run_until_complete(run_test())

    def test_collect(self):
        async def run_test():
            await self.cache_manager.put("key7", "value7", expires_in=1)
            await self.cache_manager.put("key8", "value8", expires_in=3)
            # await asyncio.sleep(2)
            await self.cache_manager.collect()
            value1 = await self.cache_manager.get("key7")
            value2 = await self.cache_manager.get("key8")
            self.assertIsNone(value1)
            self.assertEqual(value2, "value8")

        self.loop.run_until_complete(run_test())

if __name__ == '__main__':
    unittest.main()