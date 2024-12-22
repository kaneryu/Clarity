import threading
import inspect
import src.innertube.song_queue as queue
import time
import asyncio, aiohttp

import ytmusicapi
from PySide6.QtCore import QThread

mainThread: QThread = QThread.currentThread()

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


class Async_BackgroundWorker(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True
        self.stopped = False
        self.jobs = asyncio.Queue()  # Use asyncio.Queue to manage jobs
        self.semaphore = asyncio.Semaphore(10)
        
        
    def run(self):
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        event_loop.run_until_complete(self.Arun())
        

    async def Arun(self):
        print("Async-bgworker", self.is_alive())
        self.session = aiohttp.ClientSession()
        self.API = ytmusicapi.YTMusic(requests_session=self.session)
        while not self.stopped:
            await asyncio.sleep(1/15)  # 15hz
            while not self.jobs.empty():
                job = await self.jobs.get()
                fun = job["func"]
                args = job["args"]
                kwargs = job["kwargs"]

                if asyncio.iscoroutinefunction(fun):
                    async with self.semaphore:
                        await fun(*args, **kwargs)
                else:
                    fun(*args, **kwargs)
                self.jobs.task_done()

    async def add_job(self, func, *args, **kwargs):
        await self.jobs.put({"func": func, "args": args, "kwargs": kwargs})

    def add_job_sync(self, func, usestar = True, a = [], kw = {}, *args, **kwargs):
        if usestar:
            self.jobs.put_nowait({"func": func, "args": args, "kwargs": kwargs})
        else:
            self.jobs.put_nowait({"func": func, "args": a, "kwargs": kw})
        
    def stop(self):
        self.stopped = True
        print("async background worker stopped")
        asyncio.create_task(self.session.close())
      
bgworker = BackgroundWorker()
bgworker.start()

asyncBgworker = Async_BackgroundWorker()
asyncBgworker.start()