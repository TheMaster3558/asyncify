import asyncio
import functools
import sys

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Optional, TypeVar

from .utils import Semaphore

if sys.version_info >= (3, 10):
    from typing import Concatenate, ParamSpec
else:
    from typing_extensions import Concatenate, ParamSpec

if sys.version_info >= (3, 9):
    from collections.abc import Callable, Coroutine
else:
    from typing import Callable, Coroutine


P = ParamSpec('P')
T = TypeVar('T')


sentinel: Any = object()

_semaphore = Semaphore(value=None)


def set_max_threads(max_threads: int) -> None:
    """
    Set the limit on the amount of threads this library can use.

    Parameters
    -----------
    max_threads: int
        The max amount of threads.

    .. note::
        This does not limit the amount of threads used by an external library.
    """
    # instead of using our own ThreadPoolExecutor instance
    # we just use a semaphore
    # in case a user sets executor to their own or None

    global _semaphore
    _semaphore = Semaphore(max_threads)


def asyncify_func(func: Callable[P, T]) -> Callable[Concatenate[ThreadPoolExecutor, P], Coroutine[Any, Any, T]]:
    """
    Make a synchronous function into an asynchronous function by running it in a separate thread.

    Example
    --------
    .. code:: py

        import asyncify
        import requests

        @asyncify.asyncify_func
        def get(url: str) -> str:
            return requests.get(url).text

        # `get` is no longer a blocking function
        # it is now a coroutine function

        async def main():
            text = await get('https://python.org')

        # this is very useful to turn a blocking library into an async library
        get = asyncify(requests.get)
    """

    @functools.wraps(func)
    async def async_func(executor: Optional[ThreadPoolExecutor] = sentinel, *args: P.args, **kwargs: P.kwargs) -> T:
        if executor is sentinel:
            executor = None
        elif not isinstance(executor, ThreadPoolExecutor):
            args = list(args)  # type: ignore  # ParamSpecArgs no longer inherits from list, so it failed
            args.insert(0, executor)  # type: ignore  # type checker still things args is P.args

            executor = None

        new_func = functools.partial(func, *args, **kwargs)
        async with _semaphore:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(executor, new_func)

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
