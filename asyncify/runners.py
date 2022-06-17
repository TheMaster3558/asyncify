import asyncio
from typing import Any, Coroutine, TypeVar


__all__ = (
    'run',
)


T = TypeVar('T')


def run(coro: Coroutine[Any, Any, T], *, debug: bool = False) -> T:
    """
    An implementation of `asyncio.run <https://docs.python.org/3/library/asyncio-task.html?highlight=asyncio%20run#asyncio.run>`_
    for users below `Python 3.7`.

    .. note::
        This is very similar to Python 3.7's original `asyncio.run`


    Parameters
    -----------
    coro: ``Coroutine``
        The coroutine to run.
    debug: :class:`bool`
        Whether to run the event loop in debug mode.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        pass
    else:
        raise RuntimeError('Cannot call run() from a running event loop.')

    if not asyncio.iscoroutine(coro):
        raise TypeError('Expected coroutine, not {!}'.format(coro))

    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        loop.set_debug(debug)

        return loop.run_until_complete(coro)
    finally:
        try:
            tasks = asyncio.all_tasks(loop)

            for task in tasks:
                task.cancel()

            loop.run_until_complete(
                asyncio.gather(*tasks, loop=loop, return_exceptions=True)
            )

            for task in tasks:
                if task.cancelled():
                    continue
                if task.exception() is not None:
                    loop.call_exception_handler({
                        'message': 'unhandled exception during asyncio.run() shutdown',
                        'exception': task.exception(),
                        'task': task,
                    })

            loop.run_until_complete(loop.shutdown_asyncgens())

            try:
                loop.run_until_complete(loop.shutdown_default_executor())
            except AttributeError:
                pass
        finally:
            asyncio.set_event_loop(None)
            loop.close()
