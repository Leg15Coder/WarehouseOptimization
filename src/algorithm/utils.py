import asyncio


def run_async_thread(executor=None):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            return await asyncio.get_running_loop().run_in_executor(
                executor, lambda: func(*args, **kwargs)
            )
        return wrapper
    return decorator
