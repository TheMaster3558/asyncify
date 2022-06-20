import asyncio
import functools
import sys
from typing import TYPE_CHECKING, Any, Callable, Tuple, Type, TypeVar

if TYPE_CHECKING:
    from typing_extensions import ParamSpec


__all__ = ('EventsEventLoopPolicy',)


T = TypeVar('T')

if TYPE_CHECKING:
    P = ParamSpec('P')
else:
    P = TypeVar('P')


_valid_names: Tuple[str, ...] = (
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

    .. warning::
        `asyncio.get_event_loop` won't call its event if there is a running and set event loop.

    .. versionadded:: 1.1
    """

    def event(self, func: "Callable[P, Any]"):
        """|deco|

        Register a function to be called when an event loop policy method is called.
        The name of the functions should match the event loop policy method.
        the valid names are ``get_event_loop``, ``set_event_loop``, ``new_event_loop``,
        ``get_child_watcher``, ``set_child_watcher``

        Example
        ---------
        .. code:: py

            @policy.event
            def new_event_loop():
                print('New event loop being created.')

        .. note::
            Using it multiple times on the same method will overwrite the old one.
        """
        if not callable(func):
            raise TypeError('Expected a callable function, not {!r}'.format(func))

        if sys.platform == 'win32' and func.__name__ in ('get_child_watcher', 'set_child_watcher'):
            raise RuntimeError('{!r} is not supported on windows.'.format(func.__name__))

        if func.__name__ not in _valid_names:
            raise RuntimeError('{!r} is not a valid function name. {!r} are valid.'.format(func.__name__, _valid_names))

        old: Callable[..., T] = getattr(super(), func.__name__)

        @functools.wraps(old)
        def updated(*args: "P.args", **kwargs: "P.kwargs") -> T:
            func(*args, **kwargs)
            return old(*args, **kwargs)

        setattr(self, old.__name__, updated)

        return updated

    @classmethod
    def change_base_policy(cls, policy_cls: Type[asyncio.AbstractEventLoopPolicy]):
        """
        The actual things the event loop policy does are based on your platform.
        The default base loop policy is
        `asyncio.DefaultLoopPolicy <https://docs.python.org/3/library/asyncio-policy.html#asyncio.DefaultEventLoopPolicy>`_
        but can be changed.

        Parameters
        ------------
        policy_cls: Type[:class:`asyncio.AbstractEventLoopPolicy`]
            This class must inherit from
            `asyncio.AbstractEventLoopPolicy <https://docs.python.org/3/library/asyncio-policy.html#asyncio.AbstractEventLoopPolicy>`_


        This example uses `uvloop`.

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
        """
        if asyncio.AbstractEventLoop not in policy_cls.__bases__:
            raise TypeError('policy_cls must inherited from asyncio.AbstractEventLoopPolicy')

        cls.__bases__ = (policy_cls,)
