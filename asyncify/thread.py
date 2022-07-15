from __future__ import annotations

import asyncio
import threading
import queue
from typing import TYPE_CHECKING, Any, Coroutine, Tuple, Type, TypeVar, Optional

if TYPE_CHECKING:
    import concurrent.futures
    from types import TracebackType
    from typing_extensions import Self


__all__ = ('ThreadCoroutineExecutor',)


T = TypeVar('T')


class ThreadCoroutineExecutor(threading.Thread):
    def __init__(self, wait: bool = False):
        super().__init__()
        self._running = False
        self.wait = wait

        self._queue: queue.SimpleQueue[Tuple[asyncio.Future[Any], Coroutine[Any, Any, Any]]] = queue.SimpleQueue()
        self._unfinished_futures = []

        self._loop = asyncio.new_event_loop()

    def start(self) -> None:
        self._running = True
        super().start()

    def run(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def close(self) -> None:
        self._running = False
        self._loop.call_soon_threadsafe(self._loop.stop)

    def execute(self, coro: Coroutine[Any, Any, T]) -> asyncio.Future[T]:
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
            await asyncio.gather(*self._unfinished_futures)
        finally:
            self.close()
