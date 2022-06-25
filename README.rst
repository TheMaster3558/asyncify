Asyncify
=========

A python library to make things async for asyncio!


Documentation
---------------
https://asyncify.readthedocs.io/en/latest/


Installation
--------------
Python 3.7 or higher is required

.. code:: sh

    $ pip install -U asyncify-python


Example
--------
.. code:: py

    import asyncify
    import requests

    @asyncify.asyncify_func
    def get(url: str) -> str:
        return requests.get(url).text

    # `get` is no longer a blocking function
    # it is now a coroutine function

    async def main():
        text = await get('https://python.org')

    # this is very useful to turn a blocking library into an async library
    get = asyncify(requests.get)
