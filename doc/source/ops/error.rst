:mod:`ops.error` --- Contains exception classes for operation errors
====================================================================

.. automodule:: ops.error

Value-related Errors
""""""""""""""""""""
The exception classes in this section also extend :exc:`ValueError`.

.. autoclass:: InvalidHeatingCurrentError()
.. autoclass:: InvalidTargetTemperatureError()
.. autoclass:: InvalidHeaterPositionError()

State-related Errors
""""""""""""""""""""
.. autoclass:: NotCalibratedError()
.. autoclass:: RequiresSimulationError()

Locking-related Errors
""""""""""""""""""""""
.. autoclass:: LockingError()
.. autoclass:: SystemLockedError()
.. autoclass:: SystemNotLockedError()
.. autoclass:: WrongKeyError()

