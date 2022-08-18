from __future__ import annotations

import asyncio
import threading
from typing import TYPE_CHECKING, Any, Coroutine, List, Type, TypeVar, Optional

if TYPE_CHECKING:
    from types import TracebackType
    from typing_extensions import Self


__all__ = ('ThreadCoroutineExecutor',)


T = TypeVar('T')


class ThreadCoroutineExecutor(threading.Thread):
    """
    Run coroutines in separate threads easily!

    .. versionadded:: 2.0

    Parameters
    -----------
    wait: :class:`bool`
        Whether to wait for all tasks to finish before exiting context manager. Defaults to ``False``.

    Example
    --------
    .. code:: py

        import asyncify
        from aioconsole import aexec

        async def main():
            async with asyncify.ThreadCoroutineExecutor(wait=True) as thread:
                while True:
                    code = input('Type code here: ')
                    # if code is 'import time; time.sleep(5); print('Done') it will block the event loop
                    # the solution is to run it in a separate thread
                    thread.execute(aexec(code))
    """

    def __init__(self, wait: bool = False):
        super().__init__()
        self.wait = wait
        self._running: bool = False
        self._unfinished_futures: List[asyncio.Future[Any]] = []
        self._loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()

    def is_running(self) -> bool:
        """
        Whether the event loop is running in the thread.

        Returns
        -------
        :class:`bool`
        """
        return self._running and self._loop.is_running()

    def start(self) -> None:
        """
        Start the thread and its event loop.

        .. note::
            It is recommended to use `async with` instead.
        """
        self._running = True
        super().start()

    def run(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def close(self) -> None:
        """
        Close the event loop and the thread will join the main thread.

        .. warning::
            If this is called manually, all tasks will be cancelled regardless of if ``wait`` is ``True``.
            The ``async with`` context manager is meant to wait for the tasks.
        """
        self._running = False
        self._loop.call_soon_threadsafe(self._loop.close)

    def execute(self, coro: Coroutine[Any, Any, T]) -> asyncio.Future[T]:
        """
        Execute a coroutine within the thread.

        Parameters
        ----------
        coro: ``Coroutine``
            The coroutine to execute. It must be a coroutine.

        Returns
        -------
        :class:`asyncio.Future`
        """
        future = asyncio.wrap_future(asyncio.run_coroutine_threadsafe(coro, self._loop))
        self._unfinished_futures.append(future)
        future.add_done_callback(self._remove_from_unfinished)
        return future

    def _remove_from_unfinished(self, future: asyncio.Future[Any]) -> None:
        try:
            self._unfinished_futures.remove(future)
        except ValueError:
            pass

    async def __aenter__(self) -> Self:
        self.start()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        try:
            if self.wait:
                await asyncio.gather(*self._unfinished_futures)
        finally:
            self.close()
