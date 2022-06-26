from typing import TYPE_CHECKING, Any, Awaitable, Coroutine, Callable, Type, TypeVar

if TYPE_CHECKING:
    from typing_extensions import TypeAlias


T = TypeVar('T')

Coro = Coroutine[Any, Any, T]

CallableT = TypeVar('CallableT', bound=Callable[..., Any])
TypeT = TypeVar('TypeT', bound=Type[Any])

NoArgAwaitable: "TypeAlias" = Callable[[], Awaitable[T]]
