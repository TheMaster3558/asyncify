import asyncio
from typing import Optional


class Semaphore(asyncio.Semaphore):
    """A modified version of a semaphore to allow a value of ``None``"""
    def __init__(self, value: Optional[int]):
        if value is None:
            semaphore = None
        else:
            semaphore = asyncio.Semaphore(value)

        self.semaphore: Optional[asyncio.Semaphore] = semaphore

    async def acquire(self):
        if self.semaphore is not None:
            await self.semaphore.acquire()

    def release(self) -> None:
        if self.semaphore is not None:
            self.semaphore.release()
