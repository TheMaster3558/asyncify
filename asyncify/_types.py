from typing import Any, Awaitable, Coroutine, Callable, Type, TypeVar


T = TypeVar('T')

Coro = Coroutine[Any, Any, T]

CallableT = TypeVar('CallableT', bound=Callable[..., Any])
TypeT = TypeVar('TypeT', bound=Type[Any])

NoArgAwaitable = Callable[[], Awaitable[T]]
