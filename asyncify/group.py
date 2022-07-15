from __future__ import annotations

import asyncio
import enum
import inspect
from typing import (
    TYPE_CHECKING,
    Any,
    Generator,
    Generic,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    overload,
    Union,
)

if TYPE_CHECKING:
    from types import TracebackType
    from typing_extensions import Literal, Self
    from ._types import Coro


__all__ = ('TaskGroup',)


T = TypeVar('T')


class _States(enum.Enum):
    NOT_STARTED = 'NOT_STARTED'
    RUNNING = 'RUNNING'
    FINISHED = 'FINISHED'
    TIMEOUTED = 'TIMEOUTED'


class TaskGroup(Generic[T]):
    """
    Group tasks together!

    .. versionadded:: 2.0

    Parameters
    -----------
    timeout_in: Optional[:class:`float`]
        A timeout for the tasks. On the timeout all tasks are cancelled and :exc:`asyncio.TimeoutError` is raised.

    Example
    --------
    .. code:: py

        import asyncify
        import aiohttp

        async def python(session, method):
            async with session.request(method, 'https://python.org') as resp:
                resp.raise_for_status()
                return resp.status

        async def main():
            async with aiohttp.ClientSession() as session:
                async with asyncify.TaskGroup() as group:
                    group.create_task(get('https://docs.python.org/', session))
                    group.create_task(get('https://non-existent-website.com/', session))

            for task_id, result in group.get_results(return_exceptions=True):
                print(task_id)  # 0 then 1
                print(type(result))  # first time is <class 'int'>
                # second is <class 'aiohttp.client_exceptions.ClientConnectorError'>
    """

    def __init__(self, *, timeout_in: Optional[float] = None):
        self._unscheduled: List[Coro[T]] = []
        self._pending_tasks: List[Tuple[int, asyncio.Task[T]]] = []
        self._finished_tasks: List[Tuple[int, asyncio.Task[T]]] = []

        self._state: _States = _States.NOT_STARTED

        self._handle: Optional[asyncio.Handle] = None
        if timeout_in:
            self.change_timeout(timeout_in)

    def __raise_timeout(self) -> None:
        if self._state is not _States.FINISHED:
            self._state = _States.TIMEOUTED
            self.cancel_all_tasks()

    def change_timeout(self, timeout_in: float):
        if self._state not in (_States.NOT_STARTED, _States.RUNNING):
            raise RuntimeError('TaskGroup has already finished.')

        if self._handle:
            self._handle.cancel()

        loop = asyncio.get_running_loop()
        self._handle = loop.call_later(timeout_in, self.__raise_timeout)

    @property
    def pending_tasks(self) -> Tuple[Tuple[int, asyncio.Task[T]], ...]:
        """
        The tasks that have not finished yet.

        Returns
        --------
        Tuple[Tuple[:class:`int`, :class:`asyncio.Task`]]. The first item in each tuple is the order the task got scheduled in. The smaller the number the earlier.
        """
        return tuple(self._pending_tasks)

    @property
    def finished_tasks(self) -> Tuple[Tuple[int, asyncio.Task[T]], ...]:
        """
        The tasks that have finished or been cancelled.

        Returns
        --------
        Tuple[Tuple[:class:`int`, :class:`asyncio.Task`]]. The first item in each tuple is the order the task got scheduled in. The smaller the number the earlier.
        """
        return tuple(self._finished_tasks)

    @property
    def all_tasks(self) -> Tuple[Tuple[int, asyncio.Task[T]], ...]:
        """
        All the tasks in the TaskGroup.

        Returns
        --------
        Tuple[Tuple[:class:`int`, :class:`asyncio.Task`]]. The first item in each tuple is the order the task got scheduled in. The smaller the number the earlier.
        """
        return self.pending_tasks + self.finished_tasks

    @overload
    def get_results(self, *, return_exceptions: Literal[False]) -> Generator[Tuple[int, T], None, None]:
        ...

    @overload
    def get_results(
        self, *, return_exceptions: Literal[True]
    ) -> Generator[Tuple[int, Union[T, Exception]], None, None]:
        ...

    def get_results(
        self, *, return_exceptions: bool = False
    ) -> Generator[Tuple[int, Union[T, Exception]], None, None]:
        """
        Get the results of the tasks in the TaskGroup.

        Parameters
        ----------
        return_exceptions: class:`bool`
            Whether to return the exceptions or if they should be re-raised.

        Returns
        -------
        A generator that yields Tuple[:class:`int`, ``Any``], the first item in each tuple is the order the task got scheduled in. The smaller the number the earlier.
        """
        if self._state is not _States.FINISHED:
            raise RuntimeError('TaskGroup is not finished yet.')

        for task_id, task in self._finished_tasks:
            try:
                result = task.result()
            except asyncio.InvalidStateError as exc:
                raise RuntimeError('TaskGroup results fetched before tasks are finished.') from exc
            except Exception as exc:
                if not return_exceptions:
                    raise exc
                result = exc

            yield task_id, result

    def create_task(self, coro: Coro[T]) -> Optional[asyncio.Task[T]]:
        """
        Wrap a coroutine into a task, schedule it, and bind it to a TaskGroup.
        If the TaskGroup has not been started with `async with` yet, it will add the coroutine to be
        scheduled with it is started. In this case it will not return :class:`asyncio.Task`

        Parameters
        ----------
        coro: :class:`Coroutine`
            The coroutine to schedule.

        Returns
        -------
        Optional[:class:`asyncio.Task`]
        """
        if self._state is _States.NOT_STARTED:
            self._unscheduled.append(coro)
        elif self._state is _States.FINISHED:
            raise RuntimeError('TaskGroup has already finished.')
        else:
            if not inspect.iscoroutine(coro):
                raise TypeError(f'Expected coroutine, got {coro.__class__.__name__!r}')

            task_id = len(self.all_tasks)

            task = asyncio.create_task(coro)
            self._pending_tasks.append((task_id, task))

            def add_to_finished(_: Any) -> None:
                try:
                    self._pending_tasks.remove((task_id, task))
                except ValueError:
                    pass
                self._finished_tasks.append((task_id, task))

            task.add_done_callback(add_to_finished)
            return task

    def cancel_all_tasks(self) -> None:
        """
        Cancel all currently unfinished tasks.
        """
        for _, task in self._pending_tasks:
            if not task.done():  # task should never be finished
                task.cancel()

        self._finished_tasks.extend(self._pending_tasks)
        self._pending_tasks.clear()

    async def __aenter__(self) -> Self:
        self._state = _States.RUNNING
        for coro in self._unscheduled:
            self.create_task(coro)
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        if not self._pending_tasks:
            return

        done, pending = await asyncio.wait(
            [task for _, task in self._pending_tasks], return_when=asyncio.FIRST_EXCEPTION
        )
        for task in done:
            for t_id, t in self._pending_tasks:
                if task is t:
                    self._pending_tasks.remove((t_id, t))
                    self._finished_tasks.append((t_id, t))
            try:
                task.result()
            except asyncio.CancelledError:
                if self._state is _States.TIMEOUTED:
                    raise asyncio.TimeoutError

        await self.__aexit__(exc_type, exc_val, exc_tb)
