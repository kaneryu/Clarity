import threading
import inspect
import src.innertube.song_queue as queue
import time
import asyncio, aiohttp

import ytmusicapi
from PySide6.QtCore import QThread
import src.app.pyutils as utils



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
        try:
            while not self.stopped:
                await asyncio.sleep(1/15)  # 15hz
                while not self.jobs.empty():
                    job = await self.jobs.get()
                    fun = job["func"]
                    args = job["args"]
                    kwargs = job["kwargs"]
                    callback = job.get("cb")

                    try:
                        if asyncio.iscoroutinefunction(fun):
                            async with self.semaphore:
                                res = await fun(*args, **kwargs)
                                if callback:
                                    callback(res)
                        else:
                            res = fun(*args, **kwargs)
                            if callback:
                                callback(res)
                    except Exception as e:
                        print(f"Error executing job: {e}, {fun}, {args}, {kwargs}")
                    finally:
                        self.jobs.task_done()
        finally:
            await self.session.close()

    async def add_job(self, func, callback=None, *args, **kwargs):
        job = {"func": func, "args": args, "kwargs": kwargs}
        if callback:
            job["cb"] = callback
        await self.jobs.put(job)


    def add_job_sync(self, func, callback = None, usestar = True, a = [], kw = {}, *args, **kwargs):
        if usestar:
            job = {"func": func, "args": args, "kwargs": kwargs}
            if callback:
                job["cb"] = callback
            self.jobs.put_nowait(job)
            
        else:
            job = {"func": func, "args": a, "kwargs": kw}
            if callback:
                job["cb"] = callback
            self.jobs.put_nowait(job)
    
    async def putCoverConvert(self, callback, path: str, radius: int, size: int = 50, identify: str = ""):
        d = {"path": path, "radius": radius, "size": size, "identify": identify}
        await self.jobs.put({"func": utils.convertTocover.convertToCover_path, "args": [], "kwargs": d})
    
    def putCoverConvert_sync(self, callback, path: str, radius: int, size: int = 50, identify: str = ""):
        d = {"path": path, "radius": radius, "size": size, "identify": identify}
        self.jobs.put_nowait({"func": utils.convertTocover.convertToCover_path, "args": [], "kwargs": d})
    
    def stop(self):
        self.stopped = True
        print("async background worker stopped")
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
      
bgworker = BackgroundWorker()
bgworker.start()

asyncBgworker = Async_BackgroundWorker()
asyncBgworker.start()