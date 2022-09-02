import asyncio
import datetime
from typing import Optional


async def sleep_until(until: datetime.datetime) -> None:
    """
    Sleep until a certain time.

    .. versionadded:: 1.3

    Parameters
    ----------
    until: :class:`datetime.datetime`
        The time to sleep until.

    Raises
    ------
    TypeError
        `until` is not :class:`datetime.datetime.`
    """
    if not isinstance(until, datetime.datetime):  # type: ignore
        raise TypeError(f'Expected datetime.datetime, not {type(until).__name__!r}')

    seconds = (until - datetime.datetime.now(tz=until.tzinfo)).total_seconds()
    await asyncio.sleep(seconds)


async def today_sleep_until(
    hours: Optional[int] = None, minutes: Optional[int] = None, seconds: Optional[int] = None
) -> None:
    """
    Sleep until a certain time. The difference between this and :func:`sleep_until` is that this only sleeps within the current day.

    .. versionadded:: 1.3


    Parameters
    ----------
    hours: Optional[:class:`int`]
        The hours in the time.
    minutes: Optional[:class:`int`]
        The minutes in the time.
    seconds: Optional[:class:`int`]
        The seconds in the time.


    Raises
    ------
    TypeError
        No arguments were provided.


    Example
    -------
    .. code:: py

        import asyncify

        async def main():
            await asyncify.today_sleep_until(hours=9, minutes=30)  # sleeps until 9:30 AM


    .. note::
        24 hour time is also supported.
    """
    if hours is None and minutes is None and seconds is None:
        raise TypeError('You must provide hours, minutes, or seconds.')

    if not hours:
        hours = 0
    if not minutes:
        minutes = 0
    if not seconds:
        seconds = 0

    if hours > 12:
        hours -= 12

    now = datetime.datetime.now()
    total_seconds_now = (now.hour * 3600) + (now.minute * 60) + now.second
    total_seconds = (hours * 3600) + (minutes * 60) + seconds

    sleep_time = total_seconds - total_seconds_now
    await asyncio.sleep(sleep_time)
