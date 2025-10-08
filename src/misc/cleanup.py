from typing import Callable

cleanup: dict[Callable, tuple[tuple, dict]] = {}


def addCleanup(func, *args, **kwargs):
    cleanup[func] = (args, kwargs)


def runCleanup():
    print("Running cleanup")
    for func, (args, kwargs) in cleanup.items():
        func(*args, **kwargs)
