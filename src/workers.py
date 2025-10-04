import threading
import os
import inspect
import traceback
import time
import asyncio, aiohttp
from typing import Any, Callable, Optional, overload, Dict, Literal, Union, Tuple
import logging

import ytmusicapi
from PySide6.QtCore import QThread, QThreadPool, QObject, Signal, QRunnable
import src.misc.cleanup as cleanup
from src.paths import Paths

mainThread: QThread = QThread.currentThread()

from src.misc.compiled import __compiled__

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
        self.occasionalTasks = []  # list of {"func": function, "args": args, "kwargs": kwargs, "interval": seconds, "dynamic_interval_max": seconds, "last_run": timestamp}
        self.min_interval = 1  # Minimum interval for dynamic tasks
        self.threadpool = QThreadPool.globalInstance()
        self.threadpool.setMaxThreadCount(max_threads)
        self.setObjectName("BackgroundWorker")
        self.logger = logging.getLogger("BackgroundWorker")
        cleanup.addCleanup(self.stop)

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
            current_time = time.time()
            for task in self.occasionalTasks:
                if current_time - task["last_run"] >= task["interval"] and not task["isRunning"]:
                    job_runnable = JobRunnable(task["func"], task["args"], task["kwargs"], self.logger)
                    self.threadpool.start(job_runnable)
                    task["last_run"] = current_time
                        

    def stop(self):
        self.stopped = True
        self.logger.info("BackgroundWorker stopped")
        self.threadpool.waitForDone()
        self.quit()

    def add_job(self, func, *args, **kwargs):
        job = {"func": func, "args": args, "kwargs": kwargs}
        self.jobs.append(job)

    @overload
    def add_occasional_task(self, func: Callable[..., Any], interval: int, *args, **kwargs): ...
    
    @overload
    def add_occasional_task(self, func: Callable[..., bool], *, dynamic_interval_max: int, **kwargs): ...

    def add_occasional_task(self, func: Callable[..., Any], interval: Optional[int] = None, dynamic_interval_max: Optional[int] = None, *args, **kwargs) -> None:
        """Add a task to be run occasionally in the background.
        
        The task can be scheduled to run at a fixed interval or with a dynamic interval that adjusts based on the task's success.
        The task is not guaranteed to run at the exact interval, but will run as close to it as possible depending on system load and other factors.
        \n
        For a dynamic interval, the function must return a boolean indicating success (True) or failure (False).
        If the function returns True, the interval doubles until it reaches the maximum specified by dynamic_interval_max.
        If the function returns False, the interval resets to the maximum (set in BackgroundWorker.min_interval).
        To enable dynamic interval, set dynamic_interval_max.
        You can set the starting interval with interval
        \n
        
        Args:
            func (Callable[..., Any]): The function to run.
            interval (Optional[int], optional): The interval in seconds to run the task. If dynamic interval is supplied, it's the growth rate and first interval. Defaults to None.
            dynamic_interval_max (Optional[int], optional): The maximum dynamic interval in seconds. Defaults to None.

        Raises:
            TypeError: If both interval and dynamic_interval_max are provided.
            TypeError: If the function does not have a return type of bool when using dynamic_interval_max.

        Returns:
            None
            
        """
        if interval is None and dynamic_interval_max is None:
            raise TypeError("add_occasional_task() requires at least one of 'interval' or 'dynamic_interval_max'")
        
        task = {
            "func": func, 
            "args": args, 
            "kwargs": kwargs, 
            "interval": interval or 0, 
            "last_run": 0, 
            "dynamic_interval_max": dynamic_interval_max,
            "isRunning": False
        }
        
        if dynamic_interval_max is not None:
            function_signature = inspect.signature(func)
            return_annotation = function_signature.return_annotation
            if return_annotation is inspect.Signature.empty or return_annotation is not bool:
                raise TypeError("When using 'dynamic_interval_max', the function must have a return type of 'bool'")
            task["start_interval"] = task["interval"]
            base_interval = self.min_interval if task["start_interval"] is not 0 else task["start_interval"] 
            task["interval"] = base_interval  # Start with minimum interval
            def dynamic_task_wrapper():
                base_interval = self.min_interval if task["start_interval"] is not 0 else task["start_interval"] 
                task["isRunning"] = True
                try:
                    result = func(*args, **kwargs)
                except Exception as e:
                    self.logger.error(f"Error with job {func}, {e}")
                    traceback.print_exc()
                    
                if isinstance(result, bool):
                    if result:
                        task["interval"] *= 2  # Double the interval if successful
                        if task["interval"] > dynamic_interval_max:
                            task["interval"] = dynamic_interval_max  # Cap at max interval
                    else:
                        task["interval"] = base_interval  # If not, revert to min interval
                task["isRunning"] = False
                return result
            task["func"] = dynamic_task_wrapper
        self.occasionalTasks.append(task)
    
    def remove_occasional_task(self, func: Callable[..., Any]) -> None:
        """Remove a previously added occasional task.
        
        Args:
            func (Callable[..., Any]): The function to remove from the occasional tasks.

        Returns:
            None
        """
        self.occasionalTasks = [task for task in self.occasionalTasks if task["func"] != func]
    
    def runnow(self, func) -> None:
        runnable = JobRunnable(func, (), {}, self.logger)
        self.threadpool.start(runnable, priority=1500)

class Async_BackgroundWorker(QThread):
    def __init__(self):
        QThread.__init__(self)
        self.daemon = True
        self.stopped = False
        self.jobs: asyncio.Queue = asyncio.Queue()  # Use asyncio.Queue to manage jobs
        self.semaphore = asyncio.Semaphore(10)
        self.setObjectName("Async_BackgroundWorker")
        self.logger = logging.getLogger("AsyncBackgroundWorker")
        cleanup.addCleanup(self.stop)
        
    def run(self):
        self.event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.event_loop)
        self.event_loop.run_until_complete(self.Arun())
        
    async def Arun(self):
        self.logger.info("Async_BackgroundWorker started, alive: %s", self.isRunning())
        self.session = aiohttp.ClientSession()
        if not __compiled__:
            self.API = ytmusicapi.YTMusic(requests_session=self.session)
        else:
            print("Compiled mode detected, using locale dir for ytmusicapi at:", os.path.abspath(os.path.join(Paths.ASSETSPATH, os.path.join("ytmusicapi", "locales"))))
            self.API = ytmusicapi.YTMusic(requests_session=self.session, locale_dir=os.path.abspath(os.path.join(Paths.ASSETSPATH, os.path.join("ytmusicapi", "locales"))))
        
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
            print("")
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
    
    def stop(self):
        self.stopped = True
        # Wait for all pending jobs to complete
        while not self.event_loop.is_running():
            time.sleep(1/15)
        
        self.logger.info("Async_BackgroundWorker stopped")
        self.quit()

        
      
bgworker = BackgroundWorker()
bgworker.start()

asyncBgworker = Async_BackgroundWorker()
asyncBgworker.start()