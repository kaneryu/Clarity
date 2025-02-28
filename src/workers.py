import threading
import inspect
import traceback
import time
import asyncio, aiohttp
from concurrent.futures import ThreadPoolExecutor
import logging

import ytmusicapi
from PySide6.QtCore import QThread
import src.app.pyutils as utils

mainThread: QThread = QThread.currentThread()

class BackgroundWorker(threading.Thread):
    def __init__(self, max_threads=10):
        threading.Thread.__init__(self)
        self.daemon = True
        self.stopped = False
        self.jobs: list[dict[object, list, dict]] = []  # list of {"func": function, "args": args, "kwargs": kwargs}
        self.executor = ThreadPoolExecutor(max_workers=max_threads)
        self.executor._thread_name_prefix = "BackgroundWorker"
        self.name = "BackgroundWorker"
        self.logger = logging.getLogger("BackgroundWorker")

    def run(self):
        self.logger.info("BackgroundWorker started, alive: %s", self.is_alive())
        while not self.stopped:
            time.sleep(1/15)  # 15hz
            for i in self.jobs.copy():
                fun = i["func"]
                args = i["args"]
                kwargs = i["kwargs"]
                if inspect.iscoroutinefunction(fun):
                    self.executor.submit(self.run_async, fun, *args, **kwargs)
                else:
                    self.executor.submit(self.run_sync, fun, *args, **kwargs)
                self.jobs.remove(i)

    def run_async(self, fun, *args, **kwargs):
        asyncio.run(fun(*args, **kwargs))
    
    def run_sync(self, fun, *args, **kwargs):
        try:
            fun(*args, **kwargs)
        except Exception as e:
            self.logger.error("Error executing job: %s, function: %s, args: %s, kwargs: %s", e, fun, args, kwargs)
            traceback.print_exc()

    def stop(self):
        self.stopped = True
        self.executor.shutdown(wait=True)
        self.logger.info("BackgroundWorker stopped")

    def add_job(self, func, *args, **kwargs):
        job = {"func": func, "args": args, "kwargs": kwargs}
        if inspect.iscoroutinefunction(func):
            self.executor.submit(self.run_async, func, *args, **kwargs)
        else:
            self.executor.submit(self.run_sync, func, *args, **kwargs)
        


class Async_BackgroundWorker(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True
        self.stopped = False
        self.jobs = asyncio.Queue()  # Use asyncio.Queue to manage jobs
        self.semaphore = asyncio.Semaphore(10)
        self.name = "AsyncBackgroundWorker"
        self.logger = logging.getLogger("AsyncBackgroundWorker")
        
    def run(self):
        self.event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.event_loop)
        self.event_loop.run_until_complete(self.Arun())
        
    async def Arun(self):
        self.logger.info("Async_BackgroundWorker started, alive: %s", self.is_alive())
        self.session = aiohttp.ClientSession()
        self.API = ytmusicapi.YTMusic(requests_session=self.session)
        try:
            while not self.stopped:
                await asyncio.sleep(1/60)  # 60hz
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
                        self.logger.error("Error executing job: %s, function: %s, args: %s, kwargs: %s", e, fun, args, kwargs)
                        traceback.print_exc()
                    finally:
                        self.jobs.task_done()
        finally:
            await self.session.close()
            self.logger.info("Async_BackgroundWorker session closed")
    
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
        await self.add_job(func = utils.convertTocover.convertToCover_path, callback=callback, path=path, radius=radius, size=size, identify=identify)
    
    def putCoverConvert_sync(self, callback, path: str, radius: int, size: int = 50, identify: str = ""):
        self.add_job_sync(func = utils.convertTocover.convertToCover_path, callback=callback, usestar=False, a=[path, radius, size, identify])
    
    def stop(self):
        self.stopped = True
        self.logger.info("Async_BackgroundWorker stopped")
        if hasattr(self, 'event_loop'):
            self.event_loop.call_soon_threadsafe(self.event_loop.stop)
      
bgworker = BackgroundWorker()

asyncBgworker = Async_BackgroundWorker()
asyncBgworker.start()