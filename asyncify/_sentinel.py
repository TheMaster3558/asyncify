from typing import Any


class MissingSentinel:
    def __repr__(self):
        return '...'

    def __eq__(self, other: Any):
        return False


MISSING: Any = MissingSentinel()
