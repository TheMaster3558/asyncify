import functools
from typing import Any,  NoReturn, Tuple, Type


class RaisingSentinel:
    def __init__(self, **error_on: Tuple[Type[Exception], str]):
        for name, (exc_type, exc_msg) in error_on.items():
            old = getattr(self, name, None)

            def raiser(*args: Any, **kwargs: Any) -> NoReturn:
                raise exc_type(exc_msg)

            if old:
                raiser = functools.wraps(old)
            else:
                raiser.__name__ = name

            setattr(self, name, raiser)
