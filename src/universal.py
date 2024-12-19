from src.cacheManager import cacheManager as cacheManager_module
from src.innertube import song_queue as queue
from src.innertube import search as search_module
import threading
import asyncio
import types
from hashlib import md5
import time
import inspect

def ghash(thing):
    # print("making hash for", thing, ":", md5(str(thing).encode()).hexdigest())
    return md5(str(thing).encode()).hexdigest()

globalCache = cacheManager_module.CacheManager(name="cache")
songCache = cacheManager_module.CacheManager(name="songs_cache")
imageCache = cacheManager_module.CacheManager(name="images_cache")

queueInstance = queue.queue
search = search_module.search
searchModel = search_module.BasicSearchResultsModel()
async def search_shorthand(query: str, ignore_spelling: bool = False) -> search_module.BasicSearchResultsModel:
    return await search_module.search(query, ignore_spelling = ignore_spelling, model = searchModel)

class BackgroundWorker(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True
        self.stopped = False
        self.jobs: list[dict[object, list, dict]] = [] # list of {"func": function, "args": args, "kwargs": kwargs}
        
    def run(self):
        self.queue = queue.Queue.getInstance()
        # self.queue.setQueue(["F_mq88Lw2Lo", "DyTBxPyEG_M", "I8O-BFLzRF0", "UNQTvQGVjao", "IAW0oehOi24"])
        print("bgworker", self.is_alive())
        while not self.stopped:
            time.sleep(1/15) # 15hz
            for i in self.jobs:
                fun = i["func"]
                args = i["args"]
                kwargs = i["kwargs"]
                if args:
                    if kwargs:
                        if inspect.iscoroutinefunction(fun):
                            asyncio.run(fun(*args, **kwargs))
                            self.jobs.remove(i)
                            continue
                        fun(*args, **kwargs)
                    else:
                        if inspect.iscoroutinefunction(fun):
                            asyncio.run(fun(*args))
                            self.jobs.remove(i)
                            continue
                        fun(*args)
                else:
                    if inspect.iscoroutinefunction(fun):
                        asyncio.run(fun())
                        self.jobs.remove(i)
                        continue
                    fun()
                self.jobs.remove(i)
            

    def stop(self):
        self.stopped = True
        print("background worker stopped")
        
bgworker = BackgroundWorker()
bgworker.start()