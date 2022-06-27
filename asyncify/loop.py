# inspired by discord.py's tasks extension

import asyncio
import datetime
import inspect
from typing import TYPE_CHECKING, Any, Callable, Coroutine, Generic, TypeVar, Optional

from ._sentinel import MISSING

if TYPE_CHECKING:
    from typing_extensions import ParamSpec


__all__ = ('TaskLoop', 'task_loop')


T = TypeVar('T')

if TYPE_CHECKING:
    P = ParamSpec('P')
else:
    P = TypeVar('P')


class TaskLoop(Generic[P, T]):
    """
    Run a task multiple times automatically waiting in between each run.

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

    def __init__(
        self, callback: "Callable[P, Coroutine[Any, Any, T]]", *, hours: int = 0, minutes: int = 0, seconds: int = 0
    ):
        self.callback = callback

        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds

        if self.total_seconds <= 0:
            raise ValueError('The total interval must be greater than 0.')

        self._task: "asyncio.Task[None]" = MISSING
        self._iteration: int = 0
        self._last_iteration: Optional[datetime.datetime] = None

        self._before_loop: Optional[Callable[P, Any]] = None
        self._after_loop: Optional[Callable[P, Any]] = None

    async def __call__(self, *args: "P.args", **kwargs: "P.kwargs") -> T:
        return await self.callback(*args, **kwargs)

    @property
    def task(self) -> "asyncio.Task[None]":
        """
        The :class:`asyncio.Task` the task is running in.
        """
        return self._task

    @property
    def total_seconds(self) -> int:
        """
        The total seconds between each loop.
        """
        return (self.hours * 3600) + (self.minutes * 60) + (self.seconds * 1)

    @total_seconds.setter
    def total_seconds(self, seconds: int):
        self.hours = seconds // 3600
        seconds -= self.hours * 3600

        self.minutes = seconds // 60
        seconds -= self.minutes * 60

        self.seconds = seconds

    @property
    def iteration(self) -> int:
        """
        The current iteration of the loop.
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
        The method used to get the event loop.
        """
        return asyncio.get_running_loop()

    async def _start_task(self, *args: "P.args", **kwargs: "P.kwargs") -> None:
        if self._before_loop:
            await self._before_loop(*args, **kwargs)
        try:
            while True:
                await self.callback(*args, **kwargs)
                self._iteration += 1
                self._last_iteration = datetime.datetime.now()
                await asyncio.sleep(self.total_seconds)
        finally:
            if self._after_loop:
                await self._after_loop(*args, **kwargs)

    def start(self, *args: "P.args", **kwargs: "P.kwargs") -> None:  # fix later
        """
        Start the task. Arguments passed into this function will be passed into the callback.

        .. note::
            This must be called in async context.
        """
        self._iteration = 0
        loop = self.get_loop()
        self._task = loop.create_task(self._start_task(*args, **kwargs))

    def cancel(self) -> None:
        """
        Cancel the task right away.
        """
        self._task.cancel()
        self._task = MISSING

    async def stop(self) -> None:
        """
        Wait until the next iteration finishes then cancel the task.
        """
        assert self.next_iteration is not None

        next_iteration_seconds = (self.next_iteration - datetime.datetime.now()).total_seconds()
        await asyncio.sleep(next_iteration_seconds)
        self.cancel()

    def before_loop(self, func: "Callable[P, Any]") -> "Callable[P, Any]":
        """|deco|

        A callable to call before the loop starts. The arguments must match the original callback.
        """
        if not inspect.iscoroutinefunction(func):
            raise TypeError(f'Expected a coroutine function, got {func.__class__.__name__!r}')

        self._before_loop = func
        return func

    def after_loop(self, func: "Callable[P, Any]") -> "Callable[P, Any]":
        """|deco|

        A callable to call when the loop ends. The arguments must match the original callback.
        """
        if not inspect.iscoroutinefunction(func):
            raise TypeError(f'Expected a coroutine function, got {func.__class__.__name__!r}')

        self._after_loop = func
        return func


def task_loop(
    *, hours: int = 0, minutes: int = 0, seconds: int = 0
) -> "Callable[[Callable[P, Coroutine[Any, Any, T]]], TaskLoop[P, T]]":
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
