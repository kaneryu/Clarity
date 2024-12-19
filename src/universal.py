from src.cacheManager import cacheManager as cacheManager_module
from src.innertube import song_queue as queue
import threading
import asyncio
import types
from hashlib import md5
import time

def ghash(thing):
    # print("making hash for", thing, ":", md5(str(thing).encode()).hexdigest())
    return md5(str(thing).encode()).hexdigest()

globalCache = cacheManager_module.CacheManager(name="cache")
songCache = cacheManager_module.CacheManager(name="songs_cache")
imageCache = cacheManager_module.CacheManager(name="images_cache")

queueInstance = queue.queue

class BackgroundWorker(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True
        self.stopped = False
        self.jobs: list[dict[object, list, dict]] = [] # list of {"func": function, "args": args, "kwargs": kwargs}
        
    def run(self):
        self.queue = queue.Queue.getInstance()
        self.queue.setQueue(["F_mq88Lw2Lo", "DyTBxPyEG_M", "I8O-BFLzRF0", "UNQTvQGVjao", "IAW0oehOi24"])
        print("bgworker", self.is_alive())
        while not self.stopped:
            time.sleep(1/15) # 15hz
            for i in self.jobs:
                fun = i["func"]
                args = i["args"]
                kwargs = i["kwargs"]
                if args:
                    if kwargs:
                        fun(*args, **kwargs)
                    else:
                        fun(*args)
                else:
                    fun()
                self.jobs.remove(i)
            

    def stop(self):
        self.stopped = True
        print("background worker stopped")
        
bgworker = BackgroundWorker()
bgworker.start()