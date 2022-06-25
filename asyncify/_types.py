from typing import Any, Awaitable, Coroutine, Callable, Type, TypeVar


T = TypeVar('T')

Coro = Coroutine[Any, Any, T]

CallableT = TypeVar('CallableT', bound=Callable[..., Any])
TypeT = TypeVar('TypeT', bound=Type[Any])

NoArgAwaitable = Callable[[], Awaitable[T]]


# needed to support python 3.6
def ParamSpec(*args, **kwargs):
    return ...
