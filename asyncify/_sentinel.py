from typing import Any


class MissingSentinel:
    def __str__(self):
        return '...'

    def __mul__(self, other: Any):
        return 0

    def __eq__(self, other: Any):
        return False


MISSING: Any = MissingSentinel()
