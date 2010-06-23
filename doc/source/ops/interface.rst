:mod:`ops.interface` --- Handles communication with the production system
=========================================================================

.. automodule:: ops.interface

The :class:`DeviceInterface` Class
----------------------------------
.. autoclass:: DeviceInterface()

Heating
"""""""
.. autoattribute:: DeviceInterface.heatingCurrent
.. autoattribute:: DeviceInterface.temperatureSensorVoltage
.. automethod:: DeviceInterface.startHeatingWithCurrent

Heater Movement
"""""""""""""""
.. autoattribute:: DeviceInterface.heaterPosition
.. autoattribute:: DeviceInterface.heaterTargetPosition
.. automethod:: DeviceInterface.startHeaterMovement

General Attributes
""""""""""""""""""
.. autoattribute:: DeviceInterface.isSimulation
