.. currentmodule:: asyncify

API Reference
===============

Functions
----------
.. autodecorator:: asyncify_func

|

.. autodecorator:: syncify_func

|

Classes
--------
.. autodecorator:: asyncify_class

|

.. autodecorator:: ignore

|

Iterables
----------
.. autofunction:: async_iter

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

Tasks Loop
-----------
.. autoclass:: TaskLoop
  :members:
  :exclude-members: before_loop, after_loop

  .. autodecorator:: asyncify.TaskLoop.before_loop
  .. autodecorator:: asyncify.TaskLoop.after_loop
