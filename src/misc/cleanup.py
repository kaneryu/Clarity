cleanup = {}

def addCleanup(func, *args, **kwargs):
    cleanup[func] = (args, kwargs)

def runCleanup():
    for func, (args, kwargs) in cleanup.items():
        func(*args, **kwargs)