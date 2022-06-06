import asyncio
import functools
import sys

from typing import Any, TypeVar, ParamSpec

if sys.version_info > (3, 9):
    from collections.abc import Callable, Coroutine
else:
    from typing import Callable, Coroutine


P = ParamSpec('P')
T = TypeVar('T')


def asyncify_func(func: Callable[P, T]) -> Callable[P, Coroutine[Any, Any, T]]:
    """
    Make a synchronous function into an asynchronous function by running it in a separate thread.

    Usage
    -------
    .. code:: py

        import asyncio

        import asyncify
        import requests

        @asyncify_func
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
