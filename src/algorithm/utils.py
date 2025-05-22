import asyncio
import threading
from typing import Optional


def run_async_thread(executor=None):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            return await asyncio.get_running_loop().run_in_executor(
                executor, lambda: func(*args, **kwargs)
            )
        return wrapper
    return decorator


class AsyncThreadLocker:
    def __init__(self, async_locker: asyncio.Lock, thread_locker: threading.Lock):
        self.async_locker = async_locker
        self.thread_locker = thread_locker
        self._loop = asyncio.get_event_loop()

    async def update_event_loop(self):
        self.async_locker = asyncio.Lock()

    async def __aenter__(self):
        await self._loop.run_in_executor(None, self.thread_locker.acquire)
        await self.async_locker.acquire()
        return self

    async def __aexit__(self, exc_type: Optional[type], exc: Optional[BaseException], tb: Optional[BaseException]):
        self.async_locker.release()
        self.thread_locker.release()
