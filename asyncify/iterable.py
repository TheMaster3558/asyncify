from typing import Any, Awaitable, Callable, Generator, Generic, Iterable, Iterator, List, TypeVar, Optional


__all__ = ('AsyncIterable', 'async_iter')


T = TypeVar('T')


class AsyncIterable(Generic[T]):
    def __init__(
        self,
        iterable: Iterable[T],
        *,
        before: Optional[Callable[[], Awaitable]] = None,
        after: Optional[Callable[[], Awaitable]] = None
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
    before: Optional[Callable[[], Awaitable]] = None,
    after: Optional[Callable[[], Awaitable]] = None,
) -> AsyncIterable[T]:
    """
    Asynchronously iterate through an iterable while calling a callback in before and/or each iteration.

    Parameters
    ------------
    iterable: :class:`Iterable`
        The iterable to iterator over.
    before: Optional[``Callable[<no_parameters>, Awaitable]``]
        The optional asynchronous callable for before the iteration.
    after: Optional[``Callable[<no_parameters>, Awaitable]``]
        The optional asynchronous callable for after the iteration.


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
                print('%d seconds have passed.' % number)

    Raises
    -------
    TypeError
        The object passed was not an iterable.
    """
    if not hasattr(iterable, '__iter__'):
        raise TypeError('Expected object with __iter__, not {!r}'.format(iterable))

    return AsyncIterable(iterable, before=before, after=after)
