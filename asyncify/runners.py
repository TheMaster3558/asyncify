import asyncio
import inspect
import sys
from typing import Awaitable, TypeVar, Optional


__all__ = ('run',)


T = TypeVar('T')


if sys.version_info >= (3, 7) and 'sphinx' not in sys.modules:
    from asyncio import run
else:

    def run(main: Awaitable[T], *, debug: Optional[bool] = None) -> T:
        """
        An implementation of `asyncio.run <https://docs.python.org/3/library/asyncio-task.html?highlight=asyncio%20run#asyncio.run>`_
        for users below `Python 3.7`.

        .. note::
            This is very similar to Python 3.7's original `asyncio.run` and will use `asyncio`'s run if
            the `Python` version is 3.7 or above.


        Parameters
        -----------
        main: ``Awaitable``
            The coroutine to run.
        debug: :class:`bool`
            Whether to run the event loop in debug mode.


        Raises
        -------
        RuntimeError
            There is already a running event loop.
        TypeError
            The object passed is not awaitable.

        .. versionadded:: 1.1
        """
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            pass
        else:
            raise RuntimeError('Cannot call run() from a running event loop.')

        if not inspect.isawaitable(main):
            raise TypeError('Expected awaitable, not {!r}'.format(main))

        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)

            if debug is not None:
                loop.set_debug(debug)

            return loop.run_until_complete(main)
        finally:
            try:
                tasks = asyncio.all_tasks(loop)

                for task in tasks:
                    task.cancel()

                loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))

                for task in tasks:
                    if task.cancelled():
                        continue
                    if task.exception() is not None:
                        loop.call_exception_handler(
                            {
                                'message': 'unhandled exception during asyncio.run() shutdown',
                                'exception': task.exception(),
                                'task': task,
                            }
                        )

                loop.run_until_complete(loop.shutdown_asyncgens())
            finally:
                asyncio.set_event_loop(None)
                loop.close()
