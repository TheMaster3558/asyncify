from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from types import TracebackType
    from typing_extensions import Self
    
    
MISSING: Any = object()   


class Timer:
    def __init__(self):
        self._start_time: int = MISSING
        self._end_time: int = MISSING
        self._loop: asyncio.AbstractEventLoop = MISSING
            
    def start_timer(self) -> None:
        self._loop = asyncio.get_running_loop()
        self._start_time = self._loop.time()
        
    def end_timer(self) -> None:
        self._end_time = self._loop.time()
        
    def get_time(self) -> float:
        if self._start_time is MISSING or self._end_time is MISSING:
            raise RuntimeError('Timer has not ended yet.')
        return self._end_time - self._start_time
    
    async def __aenter__(self) -> Self:
        self.start_timer()
        return self
    
    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.end_timer()
        
