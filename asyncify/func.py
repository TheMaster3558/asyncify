import asyncio
import functools
import sys

from typing import Any, TypeVar

if sys.version_info >= (3, 10):
    from typing import ParamSpec
else:
    from typing_extensions import ParamSpec

if sys.version_info >= (3, 9):
    from collections.abc import Callable, Coroutine
else:
    from typing import Callable, Coroutine


P = ParamSpec('P')
T = TypeVar('T')


def asyncify_func(func: Callable[P, T]) -> Callable[P, Coroutine[Any, Any, T]]:
    """
    Make a synchronous function into an asynchronous function by running it in a separate thread.

    Example
    --------
    .. code:: py

        import asyncio

        import asyncify
        import requests

        @asyncify.asyncify_func
        def get(url: str) -> str:
            return requests.get(url).text

        # `get` is no longer a blocking function
        # it is now a coroutine function

        async def main():
            text = await get('https://python.org')

        asyncio.run(main())

        # this is very useful to turn a blocking library into an async library
        get = asyncify(requests.get)
    """
    @functools.wraps(func)
    async def async_func(*args: P.args, **kwargs: P.kwargs) -> T:
        return await asyncio.to_thread(func, *args, **kwargs)

    return async_func


def syncify_func(func: Callable[P, Coroutine[Any, Any, T]]) -> Callable[P, T]:
    """
    Make an asynchronous function a synchronous function.

    Example
    --------
    .. code:: py

        import asyncio

        import asyncify

        @asyncify.syncify_func
        async def coroutine_func():
            await asyncio.sleep(5)
            print('Done')

        coroutine_func()  # can be directly called


    .. note::

        This is equivalent to the following:

        .. code:: py

            loop = asyncio.get_event_loop()
            loop.run_until_complete(coroutine_func())
        """
    @functools.wraps(func)
    def sync_func(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
        return loop.run_until_complete(func(*args, **kwargs))

    return sync_func
