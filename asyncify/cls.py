from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Callable, Container, Optional, Union

from .func import asyncify_func

if TYPE_CHECKING:
    from ._types import CallableT, TypeT


__all__ = ('asyncify_class', 'ignore')


def ignore(func: CallableT) -> CallableT:
    """|deco|

    Ignore a function in a class when using :func:`asyncify.asyncify_class`.
    """
    func._asyncify_ignore = True  # type: ignore # we are assigning new attribute here
    return func


def asyncify_class(
    cls: Optional[TypeT] = None,
    asyncify: Optional[Container[str]] = None,
    asyncify_ignore: Optional[Container[str]] = None,
) -> Union[TypeT, Callable[[TypeT], TypeT]]:
    """|deco|

    Parameters
    ----------
    asyncify: Container[:class:`str`]
        A container (object with `__contains__`) with the methods to asyncify.
    asyncify_ignore: Container[:class:`str`]
        A container with the methods to not asyncify.


    Turn a classes methods into async functions.
    This uses :func:`asyncify.asyncify_func`.
    This ignores methods marked with :func:`asyncify.ignore` and `dunder` methods and methods passed into `asyncify_ignore`.
    If `asyncify` is passed in, only those methods are asyncified.

    Example
    ---------
    .. code:: py

        import asyncify
        import requests

        @asyncify.asyncify_class(asyncify=('request', 'get', 'post'))  # don't asyncify random small methods
        class RequestsClient:
            def __init__(self):  # ignored by asyncify
                self.session = requests.Session()

            def request(self, method, url):  # now a coroutine function
                return self.session.request(method, url)

        # can also be used like this
        RequestsClient = asyncify.asyncify_class(requests.Session)

        client = RequestsClient()

        async def main():
            await client.request('GET', 'https://python.org')


        @asyncify.asyncify_class  # it does not need the ()
        class Foo:
            ...

    Raises
    -------
    TypeError
        The object passed was not a class or both `asyncify` and `asyncify_ignore` were passed.
    """
    if asyncify and asyncify_ignore:
        raise TypeError('Only asyncify or asyncify_ignore can be passed, not both.')

    if cls is None:

        def inner(inner_cls: TypeT) -> TypeT:
            return asyncify_class(inner_cls, asyncify=asyncify, asyncify_ignore=asyncify_ignore)  # type: ignore

        return inner

    if not TYPE_CHECKING and not inspect.isclass(cls):
        raise TypeError(f'Expected class, got {type(cls).__name__!r}')

    for name, func in inspect.getmembers(cls):
        if not inspect.isfunction(func) or getattr(func, '_asyncify_ignore', False) or name.startswith('__'):
            continue

        if asyncify is not None and name not in asyncify:
            continue
        if asyncify_ignore is not None and name in asyncify_ignore:
            continue

        func = asyncify_func(func)
        setattr(cls, name, func)

    return cls
