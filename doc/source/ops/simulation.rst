:mod:`ops.simulation` --- Simulates communication with the production system
============================================================================

.. automodule:: ops.simulation

The :class:`SimulatedDeviceInterface` Class
-------------------------------------------
.. autoclass:: SimulatedDeviceInterface()

Simulation Parameters
"""""""""""""""""""""
.. attribute:: SimulatedDeviceInterface.finalTemperatureFromCurrent 

    An instance of :class:`numpy.poly1d` that determines the temperature
    (in °C) the simulated device's heater will reach, but not exceed,
    for a given heating current (in mA).

.. attribute:: SimulatedDeviceInterface.voltageFromTemperature

    An instance of :class:`numpy.poly1d` that determines the simulated
    device's temperature sensor voltage (in V) for the given heating
    temperature (in °C).

.. autoattribute:: SimulatedDeviceInterface.tau
.. autoattribute:: SimulatedDeviceInterface.heaterMovementRate

Heating
"""""""
.. autoattribute:: SimulatedDeviceInterface.heatingCurrent
.. autoattribute:: SimulatedDeviceInterface.temperatureSensorVoltage
.. autoattribute:: SimulatedDeviceInterface.temperature
.. automethod:: SimulatedDeviceInterface.startHeatingWithCurrent

Heater Movement
"""""""""""""""
.. autoattribute:: SimulatedDeviceInterface.heaterPosition
.. autoattribute:: SimulatedDeviceInterface.heaterTargetPosition
.. automethod:: SimulatedDeviceInterface.startHeaterMovement

Testing
"""""""
.. autoattribute:: SimulatedDeviceInterface.isSimulation
.. autoattribute:: SimulatedDeviceInterface.speedFactor
