from __future__ import annotations

# inspired by discord.py's tasks extension (discord.ext.tasks)

import asyncio
import datetime
import inspect
from typing import TYPE_CHECKING, Any, Callable, Coroutine, Generic, TypeVar, Optional

from ._sentinel import MISSING

if TYPE_CHECKING:
    from typing_extensions import ParamSpec
    from ._types import Coro


__all__ = ('TaskLoop', 'task_loop')


T = TypeVar('T')
T_return = TypeVar('T_return')

if TYPE_CHECKING:
    P = ParamSpec('P')
else:
    P = TypeVar('P')


class TaskLoop(Generic[P, T]):
    """
    Run a task multiple times automatically waiting in between each run.
    **Inspired by discord.py's tasks extension (discord.ext.tasks).**

    .. versionadded:: 1.3

    Parameters
    -----------
    callback: Callable[``...``, ``Coroutine``]
        The callback to call.
    hours: :class:`int`
        The hours to wait in between each run.
    minutes: :class:`int`
        The seconds to wait in between each run.
    seconds: :class:`int`
        The seconds to wait in between each run.


    Raises
    -------
    TypeError
        `callback` is not callable or `hours`, `minutes`, or `seconds` are not all :class:`int`.
    """

    _hours: int
    _minutes: int
    _seconds: int

    def __new__(cls, *args: Any, **kwargs: Any):
        self = super().__new__(cls)
        self.hours = kwargs.get('hours', 0)
        self.minutes = kwargs.get('minutes', 0)
        self.seconds = kwargs.get('seconds', 0)
        return self

    def __init__(
        self, callback: Callable[P, Coro[T]], *, hours: int = 0, minutes: int = 0, seconds: int = 0
    ):
        self.callback = callback
        self._coro_task: asyncio.Task[T] = MISSING

        self.change_interval(hours=hours, minutes=minutes, seconds=seconds)

        self._task: asyncio.Task[None] = MISSING
        self._iteration: int = 0
        self._last_iteration: Optional[datetime.datetime] = None

        self._before_loop: Optional[Callable[P, Any]] = None
        self._after_loop: Optional[Callable[P, Any]] = None

    async def __call__(self, *args: P.args, **kwargs: P.kwargs) -> T:
        return await self.callback(*args, **kwargs)

    def _assert_time(self, old: int, name: str) -> None:
        if self.total_seconds <= 0:
            setattr(self, name, old)
            raise ValueError('The total interval must be greater than 0.')

    def change_interval(self, hours: int = 0, minutes: int = 0, seconds: int = 0):
        old_hours, old_minutes, old_seconds = self.hours, self.minutes, self.seconds

        self._hours = hours
        self._minutes = minutes
        self._seconds = seconds

        if self.total_seconds <= 0:
            if old_hours + old_minutes + old_seconds > 0:
                self.change_interval(hours=old_hours, minutes=old_minutes, seconds=old_seconds)
            raise ValueError('The total seconds need to be greater than 0.')

    @property
    def task(self) -> asyncio.Task[None]:
        """
        The :class:`asyncio.Task` the task is running in.
        """
        return self._task

    @property
    def hours(self) -> int:
        """
        :class:`int` The hours to wait in between each loop.
        """
        return self._hours

    @hours.setter
    def hours(self, new: int):
        self._assert_time(self._hours, '_hours')
        self._hours = new

    @property
    def minutes(self) -> int:
        """
        :class:`int` The minutes to wait in between each loop.
        """
        return self._minutes

    @minutes.setter
    def minutes(self, new: int):
        self._assert_time(self._hours, '_minutes')
        self._minutes = new

    @property
    def seconds(self) -> int:
        """
        :class:`int` The seconds to wait in between each loop.
        """
        return self._seconds

    @seconds.setter
    def seconds(self, new: int):
        self._assert_time(self._hours, '_seconds')
        self._seconds = new

    @property
    def total_seconds(self) -> int:
        """
        :class:`int` The total seconds between each loop.
        """
        return (self.hours * 3600) + (self.minutes * 60) + (self.seconds * 1)

    @property
    def iteration(self) -> int:
        """
        :class:`int` The current iteration of the loop.
        """
        return self._iteration

    @property
    def last_iteration(self) -> Optional[datetime.datetime]:
        """
        The :class:`datetime.datetime` object that represents the last time the callback was called in the loop.
        """
        return self._last_iteration

    @property
    def next_iteration(self) -> Optional[datetime.datetime]:
        """
        The :class:`datetime.datetime` object that represents the next time the callback will be called in the loop.
        """
        if not self.last_iteration:
            return None
        return self.last_iteration + datetime.timedelta(seconds=self.total_seconds)

    def get_loop(self) -> asyncio.AbstractEventLoop:
        """
        The method used to get the event loop. It can be overridden to change how to get the loop.
        By default it uses :func:`asyncio.get_running_loop`.
        """
        return asyncio.get_running_loop()

    async def _start_task(self, *args: P.args, **kwargs: P.kwargs) -> None:
        if self._before_loop:
            await self._before_loop(*args, **kwargs)
        try:
            while True:
                loop = self.get_loop()
                self._coro_task = loop.create_task(self.callback(*args, **kwargs))
                self._iteration += 1
                self._last_iteration = datetime.datetime.now()
                await asyncio.sleep(self.total_seconds)
        finally:
            if self._after_loop:
                await self._after_loop(*args, **kwargs)

    def start(self, *args: P.args, **kwargs: P.kwargs) -> None:
        """
        Start the task. Arguments passed into this function will be passed into the callback.

        .. note::
            This must be called in async context.

        Raises
        -------
        RuntimeError
            The TaskLoop has already been started.

        """
        if self.task is not MISSING:
            raise RuntimeError('TaskLoop is already started.')

        self._iteration = 0
        loop = self.get_loop()
        self._task = loop.create_task(self._start_task(*args, **kwargs))

    def cancel(self) -> None:
        """
        Cancel the task right away.
        """
        self._task.cancel()
        self._task = MISSING
        self._coro_task = MISSING

    async def stop(self) -> None:
        """
        Wait until the next iteration finishes then cancel the task.
        """
        assert self.next_iteration is not None

        next_iteration_seconds = (self.next_iteration - datetime.datetime.now()).total_seconds()
        await asyncio.sleep(next_iteration_seconds)
        await self._coro_task
        self.cancel()

    def before_loop(self, func: Callable[P, Coro[T_return]]) -> Callable[P, Coro[T_return]]:
        """|deco|

        A callable to call before the loop starts. The arguments must match the original callback.
        """
        if not inspect.iscoroutinefunction(func):
            raise TypeError(f'Expected a coroutine function, got {func.__class__.__name__!r}')

        self._before_loop = func
        return func

    def after_loop(self, func: Callable[P, Coro[T_return]]) -> Callable[P, Coro[T_return]]:
        """|deco|

        A callable to call when the loop ends. The arguments must match the original callback.
        """
        if not inspect.iscoroutinefunction(func):
            raise TypeError(f'Expected a coroutine function, got {func.__class__.__name__!r}')

        self._after_loop = func
        return func


def task_loop(
    *, hours: int = 0, minutes: int = 0, seconds: int = 0
) -> Callable[[Callable[P, Coroutine[Any, Any, T]]], TaskLoop[P, T]]:
    """|deco|

    Run a task multiple times automatically waiting in between each run.

    Parameters
    -----------
    hours: :class:`int`
        The hours to wait in between each run.
    minutes: :class:`int`
        The seconds to wait in between each run.
    seconds: :class:`int`
        The seconds to wait in between each run.


    Returns
    --------
    :class:`TaskLoop`


    Example
    --------
    .. code:: py

         import asyncify

         @asyncify.task_loop(hours=24)
         async def alarm():
             print('BEEP BEEP BEEP!')

         @alarm.before_loop
         async def wait():
             # wait until 8:23 AM before starting the loop
             await asyncify.today_sleep_until(hours=8, minutes=23)

         @alarm.after_loop
         async def after():
             print('Alarm has been switched off.')

         async def main():
             alarm.start()
             ...
    """
    if not all(isinstance(item, int) for item in (hours, minutes, seconds)):  # type: ignore
        raise TypeError('You must provide an integer for all arguments.')

    def decorator(func: Callable[P, Coroutine[Any, Any, T]]) -> TaskLoop[P, T]:
        if not inspect.iscoroutinefunction(func):
            raise TypeError(f'Expected a coroutine function, got {func.__class__.__name__!r}')

        return TaskLoop[P, T](func, hours=hours, minutes=minutes, seconds=seconds)

    return decorator
