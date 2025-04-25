import asyncio


def run_async_thread(func):
    async def wrapper(*args, **kwargs):
        return await asyncio.get_running_loop().run_in_executor(
            None, lambda: func(*args, **kwargs)
        )

    return wrapper
