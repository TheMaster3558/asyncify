import asyncio
import datetime

from ._sentinel import MISSING


async def sleep_until(until: datetime.datetime) -> None:
    """
    Sleep until a certain time.

    Parameters
    -----------
    until: :class:`datetime.datetime`
        The time to sleep until.

    Raises
    -------
    TypeError
        `until` is not `datetime.datetime.`
    """
    if not isinstance(until, datetime.datetime):  # type: ignore
        raise TypeError(f'Expected datetime.datetime, not {until.__class__.__name__!r}')

    seconds = (until - datetime.datetime.now(tz=until.tzinfo)).total_seconds()
    await asyncio.sleep(seconds)


async def today_sleep_until(hours: int = MISSING, minutes: int = MISSING, seconds: int = MISSING):
    """
    Sleep until a certain time. The difference between this and :func:`sleep_until` is that this only sleeps within the current day.

    Parameters
    -----------
    hours: :class:`int`
        The hours in the time.
    minutes: class:`int`
        The minutes in the time.
    seconds: class:`int`
        The seconds in the time.


    Raises
    -------
    TypeError
        No arguments were provided.
    """
    if not hours or not minutes or not seconds:
        raise TypeError('You must provide hours, minutes, or seconds.')

    now = datetime.datetime.now()
    total_seconds_now = (now.hour * 3600) + (now.minute * 60) + now.second
    total_seconds = (hours * 3600) + (minutes * 60) + (seconds * 1)

    sleep_time = total_seconds - total_seconds_now
    await asyncio.sleep(sleep_time)
