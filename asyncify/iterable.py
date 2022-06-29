from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Generator,
    Generic,
    Iterable,
    Iterator,
    List,
    NoReturn,
    TypeVar,
    Optional,
)

if TYPE_CHECKING:
    from typing_extensions import Self
    from ._types import NoArgAwaitable


__all__ = ('AsyncIterable', 'async_iter')


T = TypeVar('T')


class AsyncIterable(Generic[T]):
    __slots__ = ('iterable', 'iterator', 'before', 'after')

    def __init__(
        self,
        iterable: Iterable[T],
        *,
        before: Optional[NoArgAwaitable[Any]] = None,
        after: Optional[NoArgAwaitable[Any]] = None,
    ):
        self.iterable = iterable
        self.iterator: Optional[Iterator[T]] = None

        self.before = before
        self.after = after

    def __await__(self) -> Generator[Any, Any, List[T]]:
        return self.flatten().__await__()

    def __iter__(self) -> NoReturn:
        raise TypeError(f'{self.__class__.__name__!r} object is not iterable, use async for instead.')

    def __aiter__(self) -> "Self":
        self.iterator = iter(self.iterable)
        return self

    async def __anext__(self) -> T:
        assert self.iterator is not None

        if self.before is not None:
            await self.before()

        try:
            item = next(self.iterator)
        except StopIteration:
            self.iterator = None
            raise StopAsyncIteration

        if self.after is not None:
            await self.after()

        return item

    async def flatten(self) -> List[T]:
        return [item async for item in self]


def async_iter(
    iterable: Iterable[T],
    before: Optional[NoArgAwaitable[Any]] = None,
    after: Optional[NoArgAwaitable[Any]] = None,
) -> AsyncIterable[T]:
    """
    Asynchronously iterate through an iterable while calling an async callback before and/or after each iteration.

    Parameters
    ------------
    iterable: :class:`Iterable`
        The iterable to iterator over.
    before: Optional[``Callable[<no_parameters>, Awaitable[Any]]``]
        An optional asynchronous callable for before the iteration.
    after: Optional[``Callable[<no_parameters>, Awaitable[Any]]``]
        An optional asynchronous callable for after the iteration.


    .. note::
        `before` and `after` must not take any parameters.

    .. warning:: `before` will be called once more than `after` due to not knowing when to stop iterating until after
    `before` is called.

    Example
    ---------
    .. code:: py

        import asyncio
        import functools
        import asyncify

        async def main():
            sleep = functools.partial(asyncio.sleep, 1)

            async for number in async_iter([1, 2, 3], sleep, before=True):
                print('%d seconds have passed.' % number)

    Raises
    -------
    TypeError
        The object passed was not an iterable.
    """
    if not hasattr(iterable, '__iter__'):
        raise TypeError(f'Expected iterable object, got {iterable.__class__.__name__!r}')

    return AsyncIterable[T](iterable, before=before, after=after)
