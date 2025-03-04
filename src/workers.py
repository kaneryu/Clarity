import threading
import inspect
import traceback
import time
import asyncio, aiohttp
import logging

import ytmusicapi
from PySide6.QtCore import QThread, QThreadPool, QObject, Signal, QRunnable
import src.app.pyutils as utils

mainThread: QThread = QThread.currentThread()

class JobRunnable(QRunnable):
    def __init__(self, func, args, kwargs, logger):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.logger = logger
        
    def run(self):
        try:
            if inspect.iscoroutinefunction(self.func):
                # Handle coroutine functions
                asyncio.run(self.func(*self.args, **self.kwargs))
            else:
                # Handle synchronous functions
                self.func(*self.args, **self.kwargs)
        except Exception as e:
            self.logger.error("Error executing job: %s, function: %s, args: %s, kwargs: %s", 
                             e, self.func, self.args, self.kwargs)
            traceback.print_exc()

class BackgroundWorker(QThread):
    def __init__(self, max_threads=10):
        QThread.__init__(self)
        self.daemon = True
        self.stopped = False
        self.jobs = []  # list of {"func": function, "args": args, "kwargs": kwargs}
        self.threadpool = QThreadPool.globalInstance()
        self.threadpool.setMaxThreadCount(max_threads)
        self.setObjectName("BackgroundWorker")
        self.logger = logging.getLogger("BackgroundWorker")

    def run(self):
        self.logger.info("BackgroundWorker started, alive: %s, max threads: %s", 
                        self.isRunning(), self.threadpool.maxThreadCount())
        while not self.stopped:
            time.sleep(1/15)  # 15hz
            for i in self.jobs.copy():
                # Create a runnable job and submit it to the thread pool
                job_runnable = JobRunnable(i["func"], i["args"], i["kwargs"], self.logger)
                self.threadpool.start(job_runnable)
                self.jobs.remove(i)

    def stop(self):
        self.stopped = True
        self.logger.info("BackgroundWorker stopped")
        self.threadpool.waitForDone()
        self.quit()
        self.wait()

    def add_job(self, func, *args, **kwargs):
        job = {"func": func, "args": args, "kwargs": kwargs}
        self.jobs.append(job)

class Async_BackgroundWorker(QThread):
    def __init__(self):
        QThread.__init__(self)
        self.daemon = True
        self.stopped = False
        self.jobs = asyncio.Queue()  # Use asyncio.Queue to manage jobs
        self.semaphore = asyncio.Semaphore(10)
        self.setObjectName("Async_BackgroundWorker")
        self.logger = logging.getLogger("AsyncBackgroundWorker")
        
    def run(self):
        self.event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.event_loop)
        self.event_loop.run_until_complete(self.Arun())
        
    async def Arun(self):
        self.logger.info("Async_BackgroundWorker started, alive: %s", self.isRunning())
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
bgworker.start()

asyncBgworker = Async_BackgroundWorker()
asyncBgworker.start()