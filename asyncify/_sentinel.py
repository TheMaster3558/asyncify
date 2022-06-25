import functools
from typing import Any,  NoReturn, Tuple, Type


class _RaisingSentinel:
    def __init__(self, **error_on: Tuple[Type[Exception], str]):
        for name, (exc_type, exc_msg) in error_on:
            old = getattr(self, name)

            @functools.wraps(old)
            def raiser(*args: Any, **kwargs: Any) -> NoReturn:
                raise exc_type(exc_msg)

            setattr(self, name, raiser)




