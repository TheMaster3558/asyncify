from __future__ import annotations

import functools
import inspect
from typing import TYPE_CHECKING, Any, Callable, Coroutine, Generic, TypeVar, Union

if TYPE_CHECKING:
    from types import FrameType
    from typing_extensions import ParamSpec


__all__ = ('HybridFunction', 'hybrid_function')


T_sync = TypeVar('T_sync')
T_async = TypeVar('T_async')

if TYPE_CHECKING:
    P = ParamSpec('P')
else:
    P = TypeVar('P')


class HybridFunction(Generic[P, T_sync, T_async]):
    def __init__(
        self, name: str, sync_callback: Callable[P, T_sync], async_callback: Callable[P, Coroutine[Any, Any, T_async]]
    ):
        self._name = name

        if inspect.signature(sync_callback).parameters != inspect.signature(async_callback).parameters:
            raise TypeError('Both function signatures must be the same.')

        self.sync_callback = sync_callback
        self.async_callback = async_callback
        functools.update_wrapper(self, self.sync_callback)

    def _get_frame(self, current_frame: FrameType) -> str:
        for frame in inspect.getouterframes(current_frame):
            if not frame.code_context:
                continue

            if self._name in frame.code_context[0]:
                return frame.code_context[0]
        raise RuntimeError('Could not tell if it should call sync or async.')

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> Union[T_sync, Coroutine[Any, Any, T_async]]:
        frame = inspect.currentframe()
        assert frame is not None

        code_context = self._get_frame(frame)

        start_index = code_context.index(self._name)
        if start_index == 0:
            awaited = False
        else:
            try:
                if code_context[start_index - 6:start_index - 1] == 'await':
                    awaited = True
                else:
                    awaited = False
            except IndexError:
                awaited = False

        if not awaited:
            return self.sync_callback(*args, **kwargs)
        return self.async_callback(*args, **kwargs)


def hybrid_function(
    name: str, sync_callback: Callable[P, T_sync], async_callback: Callable[P, Coroutine[Any, Any, T_async]]
) -> HybridFunction[P, T_sync, T_async]:
    """
    Do multiple things depending on whether it was awaited or not!


    Parameters
    ----------
    name: :class:`str`
        The name of the new function.
    sync_callback: ``Callable[..., Any]``
        The callable to call if it is not awaited.
    async_callback: ``Callable[..., Coroutine]``
        The callable to call if it is awaited.


    Example
    --------
    .. code:: py

        import asyncify
        import discord  # discord.py example

        class Client(discord.Client):
            get_or_fetch_user = asyncify.hybrid_function('get_or_fetch', get_user, fetch_user)

        client = Client()

        client.get_or_fetch_user(739510612652195850)  # sync cache lookup
        await client.get_or_fetch_user(739510612652195850)  # async api call
    """
    return HybridFunction[P, T_sync, T_async](name, sync_callback, async_callback)
