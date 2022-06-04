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

BaseCallable: TypeAlias = Callable[P, T]
FutureCallable: TypeAlias = Callable[P, Awaitable[T]]
CoroutineCallable: TypeAlias = Callable[P, Coroutine[Any, Any, T]]

DecoFutureCallable: TypeAlias = Callable[[BaseCallable], FutureCallable]
DecoCoroutineCallable: TypeAlias = Callable[[BaseCallable], CoroutineCallable]


def _make_future_func(func: Callable[P, T]) -> FutureCallable:
    @functools.wraps(func)
    def future_func(*args: P.args, **kwargs: P.kwargs) -> Awaitable[T]:
        partial = functools.partial(func, *args, **kwargs)

        loop = asyncio.get_event_loop()
        return loop.run_in_executor(None, partial)

    return future_func


def _make_coro_func(func: Callable[P, T]) -> CoroutineCallable:
    @functools.wraps(func)
    async def async_func(*args: P.args, **kwargs: P.kwargs) -> T:
        partial = functools.partial(func, *args, **kwargs)

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, partial)

    return async_func


@overload
def asyncify_func(return_future: Literal[True]) -> DecoFutureCallable:
    ...


@overload
def asyncify_func(return_future: Literal[False]) -> DecoCoroutineCallable:
    ...


def asyncify_func(return_future: bool = False) -> Union[DecoFutureCallable, DecoCoroutineCallable]:
    def inner(func: Callable[P, T]) -> Union[FutureCallable, CoroutineCallable]:
        if return_future:
            func = _make_future_func(func)
        else:
            func = _make_coro_func(func)
        return func
    return inner
