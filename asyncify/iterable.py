from typing import (
    Any,
    Callable,
    Coroutine,
    Generator,
    Generic,
    Iterable,
    Iterator,
    List,
    TypeVar,
    Optional
)


__all__ = (
    'AsyncIterable',
    'async_iter'
)


T = TypeVar('T')


class AsyncIterable(Generic[T]):
    def __init__(
            self,
            iterable: Iterable[T],
            *,
            before: Optional[Callable[[], Any]] = None,
            after: Optional[Callable[[], Any]] = None
    ):
        self.iterable = iterable
        self.iterator: Optional[Iterator[T]] = None

        self.before = before
        self.after = after

    def __await__(self) -> Generator[Any, Any, List[T]]:
        return self.flatten().__await__()

    def __aiter__(self):
        self.iterator = iter(self.iterable)
        return self

    async def __anext__(self) -> T:
        assert self.iterator is not None

        if self.before is not None:
            await self.before()

        try:
            item: T = next(self.iterator)
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
        before: Optional[Callable[[], Any]] = None,
        after: Optional[Callable[[], Any]] = None
) -> AsyncIterable[T]:
    """
    Asynchronously iterate through an iterable while calling a callback in before and/or each iteration.

    Parameters
    ------------
    iterable: :class:`Iterable`
        The iterable to iterator over.
    before: Optional[``Callable[[], Any]``]
        The optional callable for before the iteration.
    after: Optional[``Callable[[], Any]``]
        The optional callable for after the iteration.


    .. note::
        `before` and `after` must not take any parameters.

    Example
    ---------
    .. code:: py

        import asyncio
        import functools
        import asyncify

        async def main():
            sleep = functools.partial(asyncio.sleep, 1)

            async for number in async_iter([1, 2, 3], sleep, before=True):
                print("%d seconds have passed." % number)
    """
    return AsyncIterable(
        iterable,
        before=before,
        after=after
    )

