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
            *, callback: Callable[[], Coroutine],
            before: bool = False,
            after: bool = True
    ):
        self.iterable = iterable
        self.iterator: Optional[Iterator[T]] = None

        self.callback = callback
        self.before = before
        self.after = after

    def __await__(self) -> Generator[Any, Any, List[T]]:
        return self.flatten().__await__()

    def __aiter__(self):
        self.iterator = iter(self.iterable)
        return self

    async def __anext__(self) -> T:
        assert self.iterator is not None

        if self.before:
            await self.callback()

        try:
            item: T = next(self.iterator)
        except StopIteration:
            self.iterator = None
            raise StopAsyncIteration

        if self.after:
            await self.callback()

        return item

    async def flatten(self) -> List[T]:
        return [item async for item in self]


def async_iter(
        iterable: Iterable[T],
        callback: Callable[[], Coroutine],
        before: bool = False,
        after: bool = True
) -> AsyncIterable[T]:
    """
    Asynchronously iterate through an iterable while calling a callback in between each iteration.

    Parameters
    ------------
    iterable: :class:`Iterable`
        The iterable to iterator over.
    callback: :class:`Callable[[], Coroutine]`
        An async function that takes no arguments to call in between iterations.
    before: :class:`bool`
        Whether to call the callback before the iteration.
    after: :class:`bool`
        Whether to call the callback after the iteration.

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

