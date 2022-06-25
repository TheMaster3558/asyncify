import asyncio
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from ._types import Coro


__all__ = ('run',)


T = TypeVar('T')


# remove in v2
def run(main: "Coro[T]", *, debug: bool = False) -> T:
    import warnings
    warnings.warn('asyncify.run has been deprecated since 1.3. Use asyncio.run instead.', category=DeprecationWarning)
    return asyncio.run(main, debug=debug)
