from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Callable, Container, Optional, Union

from .func import asyncify_func

if TYPE_CHECKING:
    from ._types import CallableT, TypeT


__all__ = ('asyncify_class', 'class_include', 'class_exclude', 'ignore')


def ignore(func: CallableT) -> CallableT:
    """|deco|

    Ignore a function in a class when using :func:`asyncify.asyncify_class`.

    .. deprecated:: 2.1
        Use :func:`class_exclude` instead.
    """
    func._asyncify_ignore = True  # type: ignore # we are assigning new attribute here
    return func


def class_include(method_names: Container[str]) -> Callable[[TypeT], TypeT]:
    """|deco|

    Select certain methods to be asyncified. All other methods will be ignored.

    Parameters
    ----------
    method_names: Container[:class:`str`]
        A container (object with `__contains__`) that can has the names of the methods to asyncify.


    .. note::
        This decorator is meant to be used directly on the class.
    """
    def inner(cls: TypeT) -> TypeT:
        cls._class_include = method_names
        return cls
    return inner


def class_exclude(method_names: Container[str]) -> Callable[[TypeT], TypeT]:
    """|deco|

    Select certain methods to not be asyncified. All other methods will be asyncified.

    Parameters
    ----------
    method_names: Container[:class:`str`]
        A container (object with `__contains__`) that can has the names of the methods to not asyncify.


    .. note::
        This decorator is meant to be used directly on the class.
    """
    def inner(cls: TypeT) -> TypeT:
        cls._class_exclude = method_names
        return cls
    return inner


def asyncify_class(
    cls: TypeT,
) -> TypeT:
    """|deco|
    Turn a classes methods into async functions.
    This uses :func:`asyncify.asyncify_func`.

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
    ValueError
        :func:`class_include` and :func:`class_exclude` were both used.
    """
    if not TYPE_CHECKING and not inspect.isclass(cls):
        raise TypeError(f'Expected class, got {type(cls).__name__!r}')

    include = getattr(cls, '_class_include', ())
    exclude = getattr(cls, '_class_exclude', ())

    if include and exclude:
        raise ValueError('@class_include and @class_exclude cannot both be used.')

    for name, func in inspect.getmembers(cls):
        if not inspect.isfunction(func) or getattr(func, '_asyncify_ignore', False) or name.startswith('__'):
            continue

        if include and name not in include:
            continue
        if exclude and name in exclude:
            continue

        func = asyncify_func(func)
        setattr(cls, name, func)

    return cls
