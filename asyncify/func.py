from __future__ import annotations

import asyncio
import inspect
import functools

from typing import TYPE_CHECKING, Any, Callable, Dict, Generic, TypeVar, Optional

if TYPE_CHECKING:
    from typing_extensions import ParamSpec, Self
    from ._types import CallableT, Coro


__all__ = ('asyncify_func', 'syncify_func', 'taskify_func')


T = TypeVar('T')

if TYPE_CHECKING:
    P = ParamSpec('P')
else:
    P = TypeVar('P')


def asyncify_func(func: Callable[P, T]) -> Callable[P, Coro[T]]:
    """|deco|

    Make a synchronous function into an asynchronous function by running it in a separate thread.

    Example
    --------
    .. code:: py

        import asyncify
        import requests

        @asyncify.asyncify_func
        def get(url):
            return requests.get(url).text

        # `get` is no longer a blocking function
        # it is now a coroutine function

        async def main():
            text = await get('https://python.org')

        # this is very useful to turn a blocking library into an async library
        get = asyncify.asyncify_func(requests.get)

    .. note::
        This function uses the default loop executor.
        Change it with `loop.set_default_executor <https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.set_default_executor>`_.

    Raises
    -------
    TypeError
        The object passed in was not a function.
    """
    if not inspect.isfunction(func):
        raise TypeError(f'Expected a callable function, got {func.__class__.__name__!r}')

    @functools.wraps(func)
    async def async_func(*args: P.args, **kwargs: P.kwargs) -> T:
        new_func = functools.partial(func, *args, **kwargs)

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, new_func)

    return async_func


def syncify_func(func: Callable[P, Coro[T]]) -> Callable[P, T]:
    """|deco|

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

    .. warning::
        There must be a running event loop to call it.

    Raises
    -------
    TypeError
        The object passed was not a coroutine function.
    """
    if not inspect.iscoroutinefunction(func):
        raise TypeError(f'Expected a callable coroutine function, got {func.__class__.__name__!r}')

    @functools.wraps(func)
    def sync_func(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError as exc:
            raise RuntimeError('There is not running event loop. Consider using asyncio.run().') from exc

        return loop.run_until_complete(func(*args, **kwargs))

    return sync_func


class taskify_func(Generic[T]):
    """|deco|

    Create an asyncio task whenever you call the function!

    .. versionadded:: 2.0

    Example
    -------
    .. code:: py

        import asyncio
        import asyncify

        @asyncify.taskify_func
        async def sleep_then_print():
            await asyncio.sleep(5)
            print('Done sleeping!')

        async def main():
            task = sleep_then_print():
            print(task) #  <class '_asyncio.Task'>

            # you can even use this as a normal coroutine function
            await sleep_then_print()


    .. warning::
        There must be a running event loop to call it.

    Raises
    -------
    TypeError
        The object passed was not a coroutine function.
    """

    def __init__(self, func: Callable[..., Coro[T]]):
        if not inspect.iscoroutinefunction(func):
            raise TypeError(f'Expected a callable coroutine function, got {func.__class__.__name__!r}')

        self.func = func
        self._done_callbacks: Dict[str, Callable[[asyncio.Task[T]], Any]] = {}

        functools.update_wrapper(self, func)

        self._instance: Optional[object] = None

    def __repr__(self) -> str:
        return f'taskify_func({self.func!r})'

    def __get__(self, instance: object, owner: type) -> Self:
        new_self = self.__class__(self.func)
        new_self._done_callbacks = self._done_callbacks
        new_self._instance = self
        return new_self

    def __call__(self, *args: Any, **kwargs: Any) -> asyncio.Task[T]:
        if self._instance:
            args = (self._instance, *args)

        task = asyncio.create_task(self.func(*args, **kwargs))

        for callback in self._done_callbacks.values():
            if self._instance:
                callback = functools.partial(callback, self._instance)  # type: ignore
            task.add_done_callback(callback)  # type: ignore
            # the type checker doesn't know that `self` needs to be manually passed in.

        return task

    def default_done_callback(self, callback: CallableT) -> CallableT:
        """|deco|

        Add a callback to be added to the tasks done callbacks with `add_done_callback <https://docs.python.org/3/library/asyncio-task.html?highlight=asyncio%20task#asyncio.Task.add_done_callback>`_.
        """
        if not TYPE_CHECKING and not inspect.isfunction(callback):
            raise TypeError(f'Expected a callable function, got {callback.__class__.__name__!r}')

        self._done_callbacks[callback.__name__] = callback
        return callback

    def remove_default_done_callback(self, name: str) -> None:
        """
        Remove a done callback that would be added to the task.

        Parameters
        ----------
        name: :class:`str`
            The name of the callback.
        """
        if name not in self._done_callbacks:
            raise RuntimeError(f'{name} is not a registered done callback.')
