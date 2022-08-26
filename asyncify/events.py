from __future__ import annotations

import asyncio
import functools
import inspect
from typing import TYPE_CHECKING, Any, Callable, Dict, Set, Tuple, Type, TypeVar

if TYPE_CHECKING:
    from typing_extensions import ParamSpec


__all__ = ('EventsEventLoopPolicy',)


T = TypeVar('T')

if TYPE_CHECKING:
    P = ParamSpec('P')
else:
    P = TypeVar('P')


_VALID_NAMES: Tuple[str, ...] = (
    'get_event_loop',
    'set_event_loop',
    'new_event_loop',
    'get_child_watcher',
    'set_child_watcher',
)


class EventsEventLoopPolicy(asyncio.DefaultEventLoopPolicy):
    """
    Call a functions whenever certain things happen in asyncio!
    This is done using the event loop policy.

    Example
    ---------
    .. code:: py

        import asyncio
        import asyncify

        policy = asyncify.EventsEventLoopPolicy()

        @policy.event
        def new_event_loop():
            print('New event loop being created.')

        asyncio.set_event_loop_policy(policy)


        async def main():
            ...

        asyncio.run(main())  # prints 'New event loop being created.'
        # asyncio.run creates an event loop with `new_event_loop`

    .. note::
        :class:`asyncify.EventsEventLoopPolicy` inherits from `asyncio.DefaultEventLoopPolicy <https://docs.python.org/3/library/asyncio-policy.html#asyncio.DefaultEventLoopPolicy>`_
        unless changed with :func:`asyncify.EventsEventLoopPolicy.change_base_policy`.

    .. warning::
        `asyncio.get_event_loop` won't call its event if there is a running and set event loop.

    .. versionadded:: 1.1
    """

    _olds: Dict[str, Callable[..., Any]] = {}

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._set_olds()
        self._registered_events: Set[str] = set()

    @classmethod
    def _set_olds(cls) -> None:
        cls._olds['get_event_loop'] = cls.get_event_loop
        cls._olds['set_event_loop'] = cls.set_event_loop
        cls._olds['new_event_loop'] = cls.new_event_loop

        if hasattr(cls, 'get_child_watcher'):
            cls._olds['get_child_watcher'] = cls.get_child_watcher
        if hasattr(cls, 'set_child_watcher'):
            cls._olds['set_child_watcher'] = cls.set_child_watcher

    def __repr__(self) -> str:
        return (
            f'<EventsEventLoopPolicy base={type(self).__bases__[0]!r},'
            f' registered_events={self._registered_events!r}>'
        )

    def event(self, func: Callable[P, T]) -> Callable[P, T]:
        """|deco|

        Register a function to be called when an event loop policy method is called.
        The name of the functions should match the event loop policy method.
        The valid names are ``get_event_loop``, ``set_event_loop``, ``new_event_loop``,
        ``get_child_watcher``, and ``set_child_watcher``.

        Example
        ---------
        .. code:: py

            @policy.event
            def new_event_loop():
                print('New event loop being created.')

        .. note::
            Using it multiple times on the same method will overwrite the old one.

        Raises
        -------
        TypeError
            `func` is not a callable.
        RuntimeError
            The name either is invalid.
        """
        if not TYPE_CHECKING and not inspect.isfunction(func):
            raise TypeError(f'Expected a callable, got {type(func).__name__!r}')

        if func.__name__ not in _VALID_NAMES:
            raise RuntimeError(f'{func.__name__!r} is not a valid function name. {_VALID_NAMES} are valid.')

        old: Callable[..., Any] = getattr(super(), func.__name__)

        @functools.wraps(old)
        def updated(*args: P.args, **kwargs: P.kwargs) -> Any:
            func(*args, **kwargs)
            return old(*args, **kwargs)

        setattr(self, old.__name__, updated)
        self._registered_events.add(old.__name__)

        return func

    def remove_event(self, name: str) -> None:
        """
        Remove an event from the callbacks that would be called.

        Parameters
        ----------
        name: class:`str`
            The name of the event.

        Raises
        -------
        RuntimeError
            `name` is not a registered event.
        """
        if name not in self._registered_events:
            raise RuntimeError(f'{name!r} is not a registered event.')

        try:
            setattr(self, name, self._olds[name])
        except KeyError:
            delattr(self, name)
        self._registered_events.remove(name)

    @classmethod
    def change_base_policy(cls, policy_cls: Type[asyncio.AbstractEventLoopPolicy]) -> None:
        """
        The actual things the event loop policy does are based on your platform.
        The default base loop policy is
        `asyncio.DefaultLoopPolicy <https://docs.python.org/3/library/asyncio-policy.html#asyncio.DefaultEventLoopPolicy>`_
        but can be changed.

        Parameters
        ------------
        policy_cls: Type[:class:`asyncio.AbstractEventLoopPolicy`]
            This class must inherit from
            `asyncio.AbstractEventLoopPolicy <https://docs.python.org/3/library/asyncio-policy.html#asyncio.AbstractEventLoopPolicy>`_.


        This example uses `uvloop`.

        Example
        --------
        .. code:: py

            import asyncio
            import asyncify
            import uvloop

            asyncify.EventsEventLoopPolicy.change_base_policy(uvloop.EventLoopPolicy)

            policy = asyncify.EventsEventLoopPolicy()

            @policy.event
            def new_event_loop():
                ...

            loop = asyncio.new_event_loop()
            print(loop)  # <uvloop.Loop running=False closed=False debug=False>

        Raises
        -------
        TypeError
            `policy_cls` does not inherit from `asyncio.AbstractEventLoopPolicy`.
        """
        if asyncio.AbstractEventLoop not in policy_cls.__bases__:
            raise TypeError('policy_cls must inherited from asyncio.AbstractEventLoopPolicy.')

        cls.__bases__: Tuple[Type[Any], ...] = (policy_cls, *cls.__bases__[1:])
        cls._set_olds()
