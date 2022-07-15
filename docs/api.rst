.. currentmodule:: asyncify

API Reference
===============

Functions
----------
.. autodecorator:: asyncify_func

|

.. autodecorator:: syncify_func

|

.. autoclass:: taskify_func
  :members:
  :exclude-members: default_done_callback

  .. autodecorator:: asyncify.taskify_func.default_done_callback()

|

Classes
--------
.. autodecorator:: asyncify_class

|

.. autodecorator:: ignore

|

Iterables
----------
.. autoclass:: AsyncIterable
  :members:

|

Events
--------
.. autoclass:: EventsEventLoopPolicy
  :members:
  :exclude-members: event

  .. autodecorator:: asyncify.EventsEventLoopPolicy.event()

|

Sleep
------
.. autofunction:: sleep_until

|

.. autofunction:: today_sleep_until

|

Hybrid
-------
.. autoclass:: HybridFunction
  :members:

|

Group
------
.. autoclass:: TaskGroup
  :members:

|

Threads
--------
.. autoclass:: ThreadCoroutineExecutor
  :members:
  :exclude-members: run

|
