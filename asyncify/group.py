from __future__ import annotations

import asyncio
import inspect
from typing import TYPE_CHECKING, Any, Coroutine, Generator, Generic, List, Tuple, TypeVar

if TYPE_CHECKING:
    from typing_extensions import Self


__all__ = ('TaskGroup',)


T = TypeVar('T')


class _States:
    NOT_STARTED = 0
    RUNNING = 1
    FINISHED = 2


class TaskGroup(Generic[T]):
    """
    Group tasks together!

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
                print(task_id)  #  first time is <class 'int'>
                # second is <class 'aiohttp.client_exceptions.ClientConnectorError'>
                print(type(result))  # 0 then 1
    """

    def __init__(self):
        self._unscheduled: List[Coroutine[Any, Any, T]] = []
        self._pending_tasks: List[Tuple[int, asyncio.Task[T]]] = []
        self._finished_tasks: List[Tuple[int, asyncio.Task[T]]] = []

        self._state: int = 0

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
        The tasks that have finished.

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

    def get_results(self, *, return_exceptions: bool = False) -> Generator[Tuple[int, T], None, None]:
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
                try:
                    result = task.result()
                except Exception as exc:
                    if not return_exceptions:
                        raise
                    result = exc

            except asyncio.InvalidStateError:
                raise RuntimeError('TaskGroup closed early.')

            yield task_id, result

    def create_task(self, coro: Coroutine[Any, Any, T]):
        """
        Wrap a coroutine into a task, schedule it, and bind it to a TaskGroup.

        Parameters
        ----------
        coro: :class:`Coroutine`
            The coroutine to schedule.

        Returns
        -------
        :class:`asyncio.Task`
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

            def add_to_finished(_):
                try:
                    self._pending_tasks.remove((task_id, task))
                except ValueError:
                    pass
                self._finished_tasks.append((task_id, task))

            task.add_done_callback(add_to_finished)
            return task

    async def __aenter__(self) -> Self:
        self._state = _States.RUNNING

        for coro in self._unscheduled:
            self.create_task(coro)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await asyncio.gather(*(task for _, task in self._pending_tasks), return_exceptions=True)
        self._state = _States.FINISHED
