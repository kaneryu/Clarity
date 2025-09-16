import unittest
import asyncio
import os
from src.cacheManager.cacheManager import CacheManager
import time

class TestCacheManager(unittest.TestCase):
    def setUp(self):
        self.cache_dir = "test_cache"
        self.cache_manager = CacheManager(self.cache_dir)

    def tearDown(self):
        if os.path.exists(self.cache_dir):
            for file in os.listdir(self.cache_dir):
                os.remove(os.path.join(self.cache_dir, file))
            os.rmdir(self.cache_dir)

    def test_put_and_get(self):
        self.cache_manager.put("key1", "value1", False)
        value = self.cache_manager.get("key1")
        self.assertEqual(value, "value1")

    def test_put_with_expiry(self):
        self.cache_manager.put("key2", "value2", byte=False, expiration=0)
        value = self.cache_manager.get("key2")
        self.assertEqual(value, False)
        
    def test_put_persistent(self):
        self.cache_manager.put("key3", "value3", False, persistent=True)
        value = self.cache_manager._load_from_disk("key3")
        self.assertEqual(value, "value3")
        
    def test_delete(self):
        self.cache_manager.put("key4", "value4", False)
        self.cache_manager.delete("key4")
        value = self.cache_manager.get("key4")
        self.assertFalse(value)

    def test_clear(self):
        self.cache_manager.put("key5", "value5", False)
        self.cache_manager.put("key6", "value6", False)
        self.cache_manager.clear()
        value1 = self.cache_manager.get("key5")
        value2 = self.cache_manager.get("key6")
        self.assertIsNone(value1)
        self.assertIsNone(value2)

    def test_collect(self):
        self.cache_manager.put("key7", "value7", byte=False, expiration=0)
        self.cache_manager.put("key8", "value8", byte=False, expiration=time.time() + 10000)
        self.cache_manager.collect()
        value1 = self.cache_manager.get("key7")
        value2 = self.cache_manager.get("key8")
        self.assertEqual(value1, False)
        self.assertEqual(value2, "value8")

if __name__ == '__main__':
    unittest.main()