import time

import pytest

from src.cacheManager import cacheManager as cacheManagerModule
from src.cacheManager.cacheManager import CacheManager


@pytest.fixture
def cache(tmp_path, request):
    """A CacheManager rooted in a throwaway directory.

    `directory` is passed explicitly rather than letting CacheManager derive one
    from `name`: that derivation uses os.pathsep, so it puts the cache in a
    literal `.:<name>` directory next to the repo root on POSIX.
    """
    name = f"test-cache-{request.node.name}"
    manager = CacheManager(name=name, directory=str(tmp_path))
    yield manager
    cacheManagerModule.caches.pop(name, None)


def test_put_and_get(cache):
    cache.put("key1", "value1", False)

    assert cache.get("key1") == "value1"


def test_get_returns_false_for_unknown_key(cache):
    assert cache.get("nosuchkey") is False


def test_get_treats_a_past_expiration_as_a_miss(cache):
    cache.put("key2", "value2", byte=False, expiration=time.time() - 10)

    assert cache.get("key2") is False


@pytest.mark.xfail(
    strict=True,
    reason=(
        "get() gates on `if self.metadata[key].get('expiration', None):`, so an "
        "expiration of 0 is falsy and reads as 'never expires'. collect() uses "
        "`< now` and does treat 0 as expired -- the two disagree."
    ),
)
def test_get_treats_expiration_zero_as_expired(cache):
    cache.put("key2b", "value2b", byte=False, expiration=0)

    assert cache.get("key2b") is False


def test_delete(cache):
    cache.put("key4", "value4", False)
    cache.delete("key4")

    assert cache.get("key4") is False


def test_clear(cache):
    cache.put("key5", "value5", False)
    cache.put("key6", "value6", False)

    cache.clear()

    assert cache.get("key5") is False
    assert cache.get("key6") is False


def test_collect_removes_only_expired_entries(cache):
    cache.put("key7", "value7", byte=False, expiration=0)
    cache.put("key8", "value8", byte=False, expiration=time.time() + 10000)

    cache.collect()

    assert cache.get("key7") is False
    assert cache.get("key8") == "value8"
