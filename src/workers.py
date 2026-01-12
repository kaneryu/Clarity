import json
import typing
import asyncio
import inspect
import traceback
import enum
import time
import logging
import queue
import aiohttp
from dataclasses import dataclass
import os

from PySide6.QtCore import (
    QObject,
    QThread,
    QRunnable,
    QThreadPool,
    QMutex,
    QMutexLocker,
)
import ytmusicapi

from src.misc.compiled import __compiled__
import src.misc.cleanup as cleanup
from src.paths import Paths


mainThread: QThread = QThread.currentThread()


globalLogger = logging.getLogger("BackgroundWorkerSystem")


def argfuncFactory(func: typing.Callable, *args, **kwargs) -> typing.Callable:
    """Create a callable wrapper that captures arguments for deferred execution.

    Args:
        func: The callable to wrap
        *args: Positional arguments to pass to func
        **kwargs: Keyword arguments to pass to func

    Returns:
        A no-argument callable that invokes func with the captured arguments
    """
    return lambda: func(*args, **kwargs)


def asyncargfuncFactory(func: typing.Callable, *args, **kwargs) -> typing.Callable:
    """Create an async callable wrapper that captures arguments for deferred execution.

    Args:
        func: The async callable to wrap
        *args: Positional arguments to pass to func
        **kwargs: Keyword arguments to pass to func
    """

    async def wrapper():
        return await func(*args, **kwargs)

    return wrapper


class ExecutionPriority(enum.IntEnum):
    LOW_PRIORITY = 0
    MEDIUM_PRIORITY = 1
    HIGH_PRIORITY = 2


class JobRunnable(QRunnable):
    """A QRunnable wrapper for executing functions in a thread pool.

    Supports both synchronous and asynchronous callables. Optionally tracks
    a root function reference for lock management.
    """

    def __init__(
        self,
        func: typing.Callable,
        rootfunc: typing.Union[typing.Callable, None] = None,
    ):
        super().__init__()
        self.func = func
        self.rootfunc = rootfunc if rootfunc else func

        self.completedCallback: typing.Union[typing.Callable, None] = None

    def run(self):
        try:
            if inspect.iscoroutinefunction(self.func):
                asyncio.run(self.func())
            else:
                self.func()
        except Exception as e:
            globalLogger.error(f"Error occurred while executing job: {e}")
            traceback.print_exc()
        if self.completedCallback:
            self.completedCallback()


@dataclass
class TimedJobSettings:
    """Configuration for a timed job with optional dynamic interval adjustment.

    Attributes:
        dynamic: If True, interval adjusts based on success/failure
        base_interval: Minimum interval in seconds
        max_interval: Maximum interval in seconds (for dynamic mode)
        growth_factor: Multiplier for interval growth on failure (dynamic mode)
        interval: Fixed interval in seconds (overrides dynamic if set)
    """

    dynamic: bool

    base_interval: int
    max_interval: int
    growth_factor: float

    interval: typing.Optional[int] = None


class TimedJobManager(QObject):
    """Manages periodic jobs with optional dynamic interval adjustment.

    Tracks jobs that should run at regular intervals. In dynamic mode,
    intervals adjust based on whether jobs return True (success) or False (failure).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.timed_jobs: typing.List[
            typing.Tuple[typing.Callable, TimedJobSettings, int, int]
        ] = []  # (func, settings, dynamicInterval, last_run_timestamp)

        self.logger = logging.getLogger("TimedJobManager")

    def addTimedJob(self, func: typing.Callable, settings: TimedJobSettings) -> None:
        """Register a function to be executed periodically.

        Args:
            func: Callable to execute. If dynamic, should return bool indicating success
            settings: Timing and behavior configuration
        """
        self.timed_jobs.append(
            (func, settings, 0, 0)
        )  # 0 is the initial last run timestamp

    def removeTimedJob(self, func: typing.Callable) -> None:
        """Unregister a timed job.

        Args:
            func: The callable previously registered with addTimedJob
        """
        self.timed_jobs = [
            (f, s, di, lr) for (f, s, di, lr) in self.timed_jobs if f != func
        ]

    def checkInTimedJobs(self, func: typing.Callable) -> bool:
        """Check if a callable is registered as a timed job.

        Args:
            func: The callable to check

        Returns:
            True if the callable is registered, False otherwise
        """
        for f, s, di, lr in self.timed_jobs:
            if f == func:
                return True
        return False

    def tick(self) -> typing.List[JobRunnable]:
        """Check and prepare jobs that are due to run.

        Returns:
            List of JobRunnables ready for execution
        """
        current_time = int(time.time())
        jobs_to_run: typing.List[JobRunnable] = []
        for i, (func, settings, dynamicInterval, last_run) in enumerate(
            self.timed_jobs
        ):
            if current_time - last_run >= (
                settings.interval if settings.interval else dynamicInterval
            ):
                self.timed_jobs[i] = (
                    func,
                    settings,
                    dynamicInterval,
                    current_time + 3500000,
                )  # temporarily block re-running by setting last_run far in future

                if settings.dynamic:

                    def wrapper(captured_func=func):
                        success = False
                        # We're also going to update the last run time here because this is when it's actually run
                        self.updateLastRan(captured_func)
                        try:
                            if inspect.iscoroutinefunction(captured_func):
                                success = asyncio.run(captured_func())
                            else:
                                success = captured_func()

                            if not isinstance(success, bool):
                                success = False  # Default to False if not boolean
                        except Exception as e:
                            globalLogger.error(f"Error in timed job: {e}")
                            traceback.print_exc()
                        self.dynamic_result(captured_func, success)

                    runnable = JobRunnable(wrapper, rootfunc=func)
                    jobs_to_run.append(runnable)

                else:

                    def default_wrapper(captured_func=func):
                        # We're also going to update the last run time here because this is when it's actually run
                        self.updateLastRan(captured_func)
                        try:
                            if inspect.iscoroutinefunction(captured_func):
                                asyncio.run(captured_func())
                            else:
                                captured_func()
                        except Exception as e:
                            globalLogger.error(f"Error in timed job: {e}")
                            traceback.print_exc()

                    runnable = JobRunnable(func)
                    jobs_to_run.append(runnable)

        self.logger.debug(
            f"Timed jobs to run: {[job.rootfunc.__name__ for job in jobs_to_run]}"
        )
        return jobs_to_run

    def updateLastRan(self, func: typing.Callable) -> None:
        """Update the last run timestamp for a timed job.

        Args:
            func: The callable whose last run time to update
        """
        current_time = int(time.time())
        for i, (f, settings, dynamicInterval, last_run) in enumerate(self.timed_jobs):
            if f == func:
                self.timed_jobs[i] = (f, settings, dynamicInterval, current_time)
                break

    def dynamic_result(self, func: typing.Callable, success: bool) -> None:
        """Update dynamic interval based on job result.

        Args:
            func: The callable that completed
            success: Whether the job succeeded
        """
        for i, (f, settings, dynamicInterval, last_run) in enumerate(self.timed_jobs):
            if f == func and settings.dynamic:
                if success:
                    try:
                        dynamicInterval = max(
                            settings.base_interval,
                            int(dynamicInterval / settings.growth_factor),
                        )
                    except ZeroDivisionError:
                        dynamicInterval = settings.base_interval
                else:
                    dynamicInterval = min(
                        settings.max_interval,
                        int(dynamicInterval * settings.growth_factor),
                    )
                self.timed_jobs[i] = (f, settings, dynamicInterval, last_run)
                break


class BackgroundWorker(QThread):
    """Singleton thread managing a priority queue of background jobs.

    Executes jobs through a QThreadPool with priority levels. Supports
    function locking to prevent concurrent execution of the same function
    and timed jobs for periodic tasks.
    """

    _instance: typing.Union["BackgroundWorker", None] = None

    def __new__(self) -> "BackgroundWorker":
        if (
            not hasattr(BackgroundWorker, "_instance")
            or BackgroundWorker._instance is None
        ):
            BackgroundWorker._instance = super(
                BackgroundWorker, BackgroundWorker
            ).__new__(BackgroundWorker)
        return BackgroundWorker._instance

    def __init__(self, parent=None):
        super().__init__(parent)
        self.thread_pool = QThreadPool.globalInstance()
        self.priority_queue: queue.PriorityQueue = queue.PriorityQueue()
        self.timed_job_manager = TimedJobManager()

        self.func_lock_set: typing.Set[typing.Callable] = set()
        self.running_funcs: typing.List[typing.Callable] = []

        self.logger = logging.getLogger("BackgroundWorker")

        self.running_funcs_mutex = QMutex()

        self.running = False

        self._job_counter = 0
        self._counter_mutex = QMutex()

        cleanup.addCleanup(self.shutdown)

    def addJob(
        self,
        func: typing.Union[typing.Callable, JobRunnable],
        priority: ExecutionPriority = ExecutionPriority.MEDIUM_PRIORITY,
    ) -> None:
        """Queue a job for background execution.

        Args:
            func: Callable or JobRunnable to execute
            priority: Execution priority (LOW, MEDIUM, or HIGH)
        """
        if isinstance(func, JobRunnable):
            job = func
        else:
            job = JobRunnable(func)

        with QMutexLocker(self._counter_mutex):
            counter = self._job_counter
            self._job_counter += 1

        # Counter ensures FIFO order within same priority
        self.priority_queue.put((priority.value, counter, job))
        if isinstance(func, JobRunnable):
            self.logger.info(
                f"Job {func.rootfunc.__name__} added with priority {priority.name}"
            )
        else:
            self.logger.info(
                f"Job {job.func.__name__} added with priority {priority.name}"
            )

    def onJobStarted(self, job: JobRunnable) -> None:
        with QMutexLocker(self.running_funcs_mutex):
            self.running_funcs.append(job.rootfunc)
            self.logger.info(f"Job {job.rootfunc.__name__} started")

    def onJobCompleted(self, job: JobRunnable) -> None:
        with QMutexLocker(self.running_funcs_mutex):
            if job.rootfunc in self.running_funcs:
                self.running_funcs.remove(job.rootfunc)
            self.logger.info(f"Job {job.rootfunc.__name__} completed")

    def run(self) -> None:
        self.running = True
        while self.running:
            if not self.priority_queue.empty():
                _, _, job = self.priority_queue.get()
                with QMutexLocker(self.running_funcs_mutex):
                    if job.rootfunc in self.func_lock_set:
                        run_allowed = job.rootfunc not in self.running_funcs
                    else:
                        run_allowed = True
                if not run_allowed:
                    self.logger.debug(
                        f"Job {job.rootfunc.__name__} is already running, re-adding to queue"
                    )
                    self.addJob(job, ExecutionPriority.HIGH_PRIORITY)
                    continue
                job.completedCallback = lambda j=job: self.onJobCompleted(j)
                self.thread_pool.start(job)
                self.onJobStarted(job)

            timed_jobs = self.timed_job_manager.tick()
            for job_func in timed_jobs:
                with QMutexLocker(self.running_funcs_mutex):
                    if job_func.rootfunc not in self.running_funcs:
                        self.addJob(job_func, ExecutionPriority.LOW_PRIORITY)
            self.msleep(100)  # Sleep briefly to prevent tight loop

    def addLockedFunction(self, func: typing.Callable) -> None:
        """Mark a function to prevent concurrent execution.

        When a function is locked, only one instance can run at a time.
        Subsequent attempts are re-queued until the first completes.

        Args:
            func: The callable to lock
        """
        self.func_lock_set.add(func)

    def shutdown(self) -> None:
        """Stop the worker thread and wait for completion."""
        self.logger.info("Shutting down BackgroundWorker...")
        self.running = False
        self.wait(5000)  # Wait for thread to exit (5 sec timeout)
        self.thread_pool.waitForDone()


class AsyncBackgroundWorker(QThread):
    """Singleton thread managing an async event loop for concurrent I/O jobs.

    Maintains an aiohttp session and ytmusicapi instance for efficient
    network operations. Limits concurrent tasks to prevent resource exhaustion.
    """

    _instance: typing.Union["AsyncBackgroundWorker", None] = None

    def __new__(cls) -> "AsyncBackgroundWorker":
        if (
            not hasattr(AsyncBackgroundWorker, "_instance")
            or AsyncBackgroundWorker._instance is None
        ):
            AsyncBackgroundWorker._instance = super(AsyncBackgroundWorker, cls).__new__(
                cls
            )
        return AsyncBackgroundWorker._instance

    def __init__(self, parent=None):
        super().__init__(parent)

        self.job_queue: asyncio.Queue = asyncio.Queue()
        self.logger = logging.getLogger("AsyncBackgroundWorker")
        self.running = False
        self.default_timeout: typing.Optional[float] = 30.0  # seconds
        self.long_running_threshold: float = 30.0  # seconds before logging warning

        self.task_metadata: typing.Dict[asyncio.Task, typing.Tuple[str, float]] = (
            {}
        )  # task -> (name, start_time)

        self.event_loop: typing.Union[asyncio.AbstractEventLoop, None] = None

        cleanup.addCleanup(self.shutdown)

    def addJob(
        self, func: typing.Callable, timeout: typing.Optional[float] = None
    ) -> None:
        """Queue an async job for execution.

        Args:
            func: Async callable to execute in the event loop
            timeout: Maximum execution time in seconds (None for no timeout, uses default_timeout if not specified)
        """
        if timeout is None:
            timeout = self.default_timeout
        self.job_queue.put_nowait((func, timeout))
        self.logger.debug(
            f"Job {func.__name__} added to async queue (timeout: {timeout}s)"
        )

    def run(self) -> None:
        asyncio.run(self.async_run())

    async def async_run(self) -> None:
        self.event_loop = asyncio.get_event_loop()
        tasks: set[asyncio.Task] = set()
        max_concurrent = 10
        self.running = True

        self.logger.info("AsyncBackgroundWorker started, alive: %s", self.isRunning())
        self.session = aiohttp.ClientSession()

        if not __compiled__:
            self.API = ytmusicapi.YTMusic(requests_session=self.session)
        else:
            print(
                "Compiled mode detected, using locale dir for ytmusicapi at:",
                os.path.abspath(
                    os.path.join(
                        Paths.ASSETSPATH, os.path.join("ytmusicapi", "locales")
                    )
                ),
            )
            self.API = ytmusicapi.YTMusic(
                requests_session=self.session,
                locale_dir=os.path.abspath(
                    os.path.join(
                        Paths.ASSETSPATH, os.path.join("ytmusicapi", "locales")
                    )
                ),
            )

        monitor_task = asyncio.create_task(  # noqa: F841
            self._monitor_long_running_tasks()
        )

        while self.running:
            if len(tasks) >= max_concurrent:
                done, tasks = await asyncio.wait(
                    tasks, return_when=asyncio.FIRST_COMPLETED
                )
            try:
                func, job_timeout = await asyncio.wait_for(
                    self.job_queue.get(), timeout=1
                )
            except TimeoutError:
                continue
            task = asyncio.create_task(self._run_job(func, job_timeout))
            tasks.add(task)
            self.task_metadata[task] = (func.__name__, time.time())

            def cleanup_task(t):
                tasks.discard(t)
                self.task_metadata.pop(t, None)

            task.add_done_callback(cleanup_task)

    async def _run_job(
        self, func: typing.Callable, timeout: typing.Optional[float]
    ) -> None:
        try:
            if inspect.iscoroutinefunction(func):
                if timeout:
                    await asyncio.wait_for(func(), timeout=timeout)
                else:
                    await func()
            else:
                func()
            self.logger.debug(f"Job {func.__name__} completed")
        except asyncio.TimeoutError:
            self.logger.error(f"Job {func.__name__} timed out after {timeout}s")
        except Exception as e:
            self.logger.error(f"Error in job {func.__name__}: {e}")
            traceback.print_exc()
        finally:
            self.job_queue.task_done()

    async def _monitor_long_running_tasks(self) -> None:
        """Periodically check for tasks exceeding the long-running threshold."""
        while self.running:
            await asyncio.sleep(10)  # Check every 10 seconds
            current_time = time.time()
            for task, (name, start_time) in list(self.task_metadata.items()):
                elapsed = current_time - start_time
                if elapsed > self.long_running_threshold:
                    self.logger.warning(
                        f"Task {name} has been running for {elapsed:.1f}s (threshold: {self.long_running_threshold}s)"
                    )

    def shutdown(self) -> None:
        """Stop the async event loop and wait for completion."""
        self.logger.info("Shutting down AsyncBackgroundWorker...")
        self.running = False
        self.wait(5000)


bgworker = BackgroundWorker()
asyncBgworker = AsyncBackgroundWorker()
