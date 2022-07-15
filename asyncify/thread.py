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
    def __init__(self, wait: bool = True):
        super().__init__()
        self._running = False
        self.wait = wait

        self._queue: queue.SimpleQueue[Tuple[asyncio.Future[Any], Coroutine[Any, Any, Any]]] = queue.SimpleQueue()
        self._unfinished_futures = []

    def start(self) -> None:
        self._running = True
        super().start()

    def run(self) -> None:
        while self._running:
            try:
                future, coroutine = self._queue.get(timeout=0.1)
            except queue.Empty:
                continue

            def set_result_or_exception(other_future: concurrent.futures.Future[Any]):
                assert other_future.done()
                try:
                    result = other_future.result()
                except BaseException as exc:
                    other_future.set_exception(exc)
                else:
                    future.set_result(result)
                try:
                    self._unfinished_futures.remove(future)
                except ValueError:
                    pass

            asyncio.run_coroutine_threadsafe(coroutine, future.get_loop()).add_done_callback(set_result_or_exception)

    def stop(self):
        self._running = False

    def execute(self, coroutine: Coroutine[Any, Any, T]) -> asyncio.Future[T]:
        future = asyncio.get_running_loop().create_future()
        self._queue.put((future, coroutine))
        self._unfinished_futures.append(future)
        return future

    async def __aenter__(self) -> Self:
        self.start()
        return self

    async def __aexit__(
            self,
            exc_type: Optional[Type[BaseException]],
            exc_val: Optional[BaseException],
            exc_tb: Optional[TracebackType],
    ) -> None:
        self.stop()
