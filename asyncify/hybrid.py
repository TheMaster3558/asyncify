from __future__ import annotations

import inspect
import re
from typing import TYPE_CHECKING, Any, Callable, Generic, Optional, TypeVar, Union

if TYPE_CHECKING:
    from types import FrameType
    from typing_extensions import Self
    from ._types import Coro


__all__ = ('HybridFunction',)


SyncT = TypeVar('SyncT')
AsyncT = TypeVar('AsyncT')


class HybridFunction(Generic[SyncT, AsyncT]):
    """
    Do multiple things depending on whether it was awaited or not!

    .. versionchanged:: 2.0
        Changed from function `hybrid_function` to class `HybridFunction`


    Parameters
    ----------
    name: :class:`str`
        The name of the new function. This must be the same as the function name to work.
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
            get_or_fetch_user = asyncify.HybridFunction(
                                'get_or_fetch_user',
                                 discord.Client.get_user,
                                 discord.Client.fetch_user
            )

        client = Client()

        client.get_or_fetch_user(739510612652195850)  # sync cache lookup
        await client.get_or_fetch_user(739510612652195850)  # async api call


    .. warning::
        Make the to name the function uniquely. Functions with the same name could be called unexpectedly.
    """

    regex = re.compile(r'await\s+(\w|\.)*\s*\(.*\)')

    def __init__(
        self,
        name: str,
        sync_callback: Callable[..., SyncT],
        async_callback: Callable[..., Coro[AsyncT]],
    ):
        if not inspect.isfunction(sync_callback):
            raise TypeError(f'Expected callable function, got {sync_callback.__class__.__name__!r}')

        if not inspect.iscoroutinefunction(async_callback):
            raise TypeError(
                f'Expected a callable coroutine function, got {async_callback.__class__.__name__!r}'
            )

        self._name = name
        self.sync_callback = sync_callback
        self.async_callback = async_callback

        self._instance: Optional[object] = None

        self.name_regex: re.Pattern[str] = re.compile(rf'\(*{self._name}\)*\s*')

    def __repr__(self) -> str:
        return f'HybridFunction({self._name!r}, {self.sync_callback!r}, {self.async_callback!r})'

    @property
    def __name__(self) -> str:
        return self._name

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and other._name == self._name
            and other.sync_callback is self.sync_callback
            and other.async_callback is self.async_callback
        )

    def __get__(self, instance: object, owner: type) -> Self:
        new_self = self.__class__(self._name, self.sync_callback, self.async_callback)
        new_self._instance = instance
        return new_self

    def _check_regex(self, code_context: str) -> bool:
        return not not self.regex.search(code_context)

    def _get_frame(self, current_frame: FrameType) -> str:
        for frame in inspect.getouterframes(current_frame):
            if not frame.code_context:
                continue
            if self.name_regex.search(frame.code_context[0]):
                return frame.code_context[0]
        raise RuntimeError('Could not tell if it should call sync or async.')

    def __call__(self, *args: Any, **kwargs: Any) -> Union[SyncT, Coro[AsyncT]]:
        if self._instance:
            args = (self._instance, *args)

        frame = inspect.currentframe()
        assert frame is not None

        code_context = self._get_frame(frame).strip()
        if self._check_regex(code_context):
            return self.async_callback(*args, **kwargs)
        return self.sync_callback(*args, **kwargs)
