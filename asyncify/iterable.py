from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Coroutine,
    Generator,
    Generic,
    Iterable,
    Iterator,
    List,
    TypeVar,
    Optional,
)

if TYPE_CHECKING:
    from typing_extensions import Self, TypeAlias


__all__ = ('AsyncIterable',)


T = TypeVar('T')
NoParamsCoroFunc: TypeAlias = Callable[[], Coroutine[Any, Any, Any]]


class AsyncIterable(Generic[T]):
    """
    Asynchronously iterate through an iterable while calling an async callback before and/or after each iteration.

    .. versionchanged:: 2.0
        Changed from function `async_iter` to class `AsyncIterable`


    Parameters
    ----------
    iterable: :class:`Iterable`
        The iterable to iterator over.
    before: Optional[``async_function``]
        An optional asynchronous callable for before the iteration.
    after: Optional[``async_function``]
        An optional asynchronous callable for after the iteration.


    .. note::
        `before` and `after` must not take any parameters.

    .. warning::
        `before` will be called once more than `after` due to not knowing when to stop iterating until after
        `before` is called.

    Example
    -------
    .. code:: py

        import asyncio
        import functools
        import asyncify

        async def main():
            sleep = functools.partial(asyncio.sleep, 1)

            async for number in asyncify.AsyncIterable([1, 2, 3], before=sleep):
                print(f'{number} seconds have passed.')

    Raises
    ------
    TypeError
        The object passed was not an iterable.
    """

    __slots__ = ('iterable', '_iterator', 'before', 'after')

    def __init__(
        self,
        iterable: Iterable[T],
        *,
        before: Optional[NoParamsCoroFunc] = None,
        after: Optional[NoParamsCoroFunc] = None,
    ):
        if not hasattr(iterable, '__iter__'):
            raise TypeError(f'Expected iterable object, got {type(self).__name__!r}')

        self.iterable = iterable
        self._iterator: Optional[Iterator[T]] = None

        self.before = before
        self.after = after

    @property
    def iterator(self) -> Optional[Iterator[T]]:
        """
        The current object that is being used for iteration.

        Returns
        -------
        Optional[:class:`Iterator`]
        """
        return self._iterator

    def __repr__(self) -> str:
        return f'AsyncIterable({self._iterator!r}, before={self.before!r}, after={self.after!r})'

    def __await__(self) -> Generator[Any, Any, List[T]]:
        return self.flatten().__await__()

    def __aiter__(self) -> Self:
        self._iterator = iter(self.iterable)
        return self

    async def __anext__(self) -> T:
        assert self._iterator is not None

        if self.before is not None:
            await self.before()

        try:
            item = next(self._iterator)
        except StopIteration:
            self._iterator = None
            raise StopAsyncIteration

        if self.after is not None:
            await self.after()

        return item

    async def flatten(self) -> List[T]:
        """
        Return a list from the result of iterating through the iterable. This still calls `before` and `after`.

        Returns
        -------
        :class:`List`
        """
        return [item async for item in self]
