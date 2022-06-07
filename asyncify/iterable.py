import asyncio
import sys

from typing import Any, Generator, Generic, TypeAlias, TypeVar, Optional

if sys.version_info >= (3, 9):
    from collections.abc import Iterable, Iterator
    from typing import List
else:
    from typing import Iterable, Iterator
    List: TypeAlias = list


T = TypeVar('T')


class AsyncIterable(Generic[T]):
    def __init__(self, iterable: Iterable[T], *, delay: float = 0):
        self.iterable = iterable
        self.iterator: Optional[Iterator[T]] = None

        self.delay = delay

    def __await__(self) -> Generator[Any, Any, List[T]]:
        return self.flatten().__await__()   # type: ignore

    def __aiter__(self):
        self.iterator = iter(self.iterable)
        return self

    async def __anext__(self) -> T:
        assert self.iterator is not None

        try:
            item: T = next(self.iterator)
        except StopIteration:
            self.iterator = None
            raise StopAsyncIteration

        await asyncio.sleep(self.delay)
        return item

    async def flatten(self) -> List[T]:
        return [item async for item in self]


def async_iter(iterable: Iterable[T], *, delay: float = 0) -> AsyncIterable[T]:
    return AsyncIterable(iterable, delay=delay)
