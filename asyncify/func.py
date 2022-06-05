import asyncio
import functools

from typing import (
    Any,
    Awaitable,
    Callable,
    Coroutine,
    Literal,
    overload,
    TypeAlias,
    TypeVar,
    ParamSpec,
    Union
)


P = ParamSpec('P')
T = TypeVar('T')


def _make_future_func(func: Callable[P, T]) -> Callable[P, Awaitable[T]]:
    @functools.wraps(func)
    def future_func(*args: P.args, **kwargs: P.kwargs) -> Awaitable[T]:
        partial = functools.partial(func, *args, **kwargs)

        loop = asyncio.get_event_loop()
        return loop.run_in_executor(None, partial)

    return future_func


def _make_coro_func(func: Callable[P, T]) -> Callable[P, Coroutine[Any, Any, T]]:
    @functools.wraps(func)
    async def async_func(*args: P.args, **kwargs: P.kwargs) -> T:
        partial = functools.partial(func, *args, **kwargs)

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, partial)

    return async_func


@overload
def asyncify_func(return_future: Literal[True]) -> Callable[[Callable[P, T]], Callable[P, Awaitable[T]]]:
    ...


@overload
def asyncify_func(return_future: Literal[False]) -> Callable[[Callable[P, T]], Callable[P, Coroutine[Any, Any, T]]]:
    ...


def asyncify_func(return_future: bool = False) -> Callable[[Callable[P, T]], Callable[P, Union[
    Awaitable[T],
    Coroutine[Any, Any, T]
]]]:
    def inner(func: Callable[P, T]) -> Callable[P, Union[Awaitable[T], Coroutine[Any, Any, T]]]:
        if return_future:
            new_func = _make_future_func(func)
        else:
            new_func = _make_coro_func(func)
        return new_func
    return inner
