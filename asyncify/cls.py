from __future__ import annotations

import inspect
from typing import TYPE_CHECKING

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


def asyncify_class(cls: TypeT) -> TypeT:
    """|deco|

    Turn a classes methods into async functions.
    This uses :func:`asyncify.asyncify_func`.
    This ignores methods marked with :func:`asyncify.ignore` and `dunder` methods.

    Example
    ---------
    .. code:: py

        import asyncify
        import requests

        @asyncify.asyncify_class
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

    Raises
    -------
    TypeError
        The object passed was not a class.
    """
    if not TYPE_CHECKING and not inspect.isclass(cls):
        raise TypeError(f'Expected class, got {cls.__class__.__name__!r}')

    for name, func in inspect.getmembers(cls):
        if not inspect.isfunction(func) or getattr(func, '_asyncify_ignore', False) or name.startswith('__'):
            continue

        func = asyncify_func(func)
        setattr(cls, name, func)

    return cls
