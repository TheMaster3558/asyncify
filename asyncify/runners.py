import asyncio
import sys
from typing import TYPE_CHECKING, Any, Coroutine, TypeVar, Optional

if TYPE_CHECKING:
    from typing_extensions import Self


__all__ = ('run', 'Runner')


T = TypeVar('T')


if sys.version_info >= (3, 7) and 'sphinx' not in sys.modules:
    from asyncio import run

else:
    class Runner:
        def __init__(self, debug: bool = False):
            self.loop: Optional[asyncio.AbstractEventLoop] = None
            self.debug = debug

        def __enter__(self) -> Self:
            self._init(debug=self.debug)
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.close()

        def run(self, main: Coroutine[Any, Any, T]) -> T:
            if self.loop is None:
                raise RuntimeError('Runner incorrectly initialized.')
            return self.loop.run_until_complete(main)

        def close(self):
            try:
                self._cancel_tasks()
                self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            finally:
                self.loop.close()
                self.loop = None
                asyncio.set_event_loop(self.loop)

        def _init(self, debug: bool = False) -> None:
            _check_loop()

            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

            self.loop.set_debug(debug)

        def _cancel_tasks(self):
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

    def run(main: Coroutine[Any, Any, T], *, debug: bool = False) -> T:
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
        with Runner(debug=debug) as runner:
            return runner.run(main)


def _check_loop() -> None:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        pass
    else:
        raise RuntimeError('Cannot call run() from a running event loop.')
