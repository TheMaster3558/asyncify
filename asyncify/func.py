import asyncio
import functools
import sys

from typing import TYPE_CHECKING, Any, Callable, Coroutine, Optional, TypeVar

if TYPE_CHECKING:
    from typing_extensions import ParamSpec
    


__all__ = (
    'asyncify_func',
    'syncify_func'
)


T = TypeVar('T')

if TYPE_CHECKING:
    P = ParamSpec('P')
else:
    P = TypeVar('P')


def asyncify_func(func: Callable[P, T]) -> Callable[P, Coroutine[Any, Any, T]]:
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
    
    .. note::
    
        This function uses the default loop executor.
        Change it with `loop.set_default_executor <https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.set_default_executor>`_.
    """

    @functools.wraps(func)
    async def async_func(*args: P.args, **kwargs: P.kwargs) -> T:
        new_func = functools.partial(func, *args, **kwargs)
        
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, new_func)

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
