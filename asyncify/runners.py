import asyncio
import sys
from typing import TYPE_CHECKING, Any, Type, TypeVar, Optional

from ._sentinel import RaisingSentinel

if TYPE_CHECKING:
    from types import TracebackType
    from typing_extensions import Self
    from ._types import Coro


__all__ = ('run',)


T = TypeVar('T')


_MISSING: Any = RaisingSentinel(__getattribute__=(RuntimeError, 'Runner was not initialized properly.'))


if sys.version_info >= (3, 7) and 'sphinx' not in sys.modules:
    from asyncio import run
else:

    class _Runner:
        def __init__(self, debug: bool = False):
            self.loop: asyncio.AbstractEventLoop = _MISSING
            self.debug = debug

        def __enter__(self) -> "Self":
            self.init(debug=self.debug)
            return self

        def __exit__(
            self,
            exc_type: Optional[Type[BaseException]],
            exc_value: Optional[BaseException],
            traceback: Optional[TracebackType],
        ) -> None:
            self.close()

        def run(self, main: "Coro[T]") -> T:
            return self.loop.run_until_complete(main)

        def close(self) -> None:
            try:
                self._cancel_tasks()
                self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            finally:
                self.loop.close()
                self.loop = _MISSING
                asyncio.set_event_loop(self.loop)

        def init(self, debug: bool = False) -> None:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

            self.loop.set_debug(debug)

        def _cancel_tasks(self) -> None:
            tasks = asyncio.all_tasks(self.loop)

            for task in tasks:
                task.cancel()

            self.loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))

            for task in tasks:
                if task.cancelled():
                    continue
                if task.exception() is not None:
                    self.loop.call_exception_handler(
                        {
                            'message': 'unhandled exception during asyncio.run() shutdown',
                            'exception': task.exception(),
                            'task': task,
                        }
                    )

    def run(main: "Coro[T]", *, debug: bool = False) -> T:
        """
        An implementation of `asyncio.run <https://docs.python.org/3/library/asyncio-task.html?highlight=asyncio%20run#asyncio.run>`_
        for users below `Python 3.7`.

        .. note::
            This is very similar to Python 3.7's original `asyncio.run` and will use `asyncio`'s run if
            the `Python` version is 3.7 or above.


        Parameters
        -----------
        main: ``Coroutine``
            The coroutine to run.
        debug: :class:`bool`
            Whether to run the event loop in debug mode.


        Raises
        -------
        RuntimeError
            There is already a running event loop.
        TypeError
            The object passed is not a coroutine.


        .. versionadded:: 1.1
        """
        _check_loop()

        with _Runner(debug=debug) as runner:
            return runner.run(main)


def _check_loop() -> None:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        pass
    else:
        raise RuntimeError('Cannot call run() from a running event loop.')
