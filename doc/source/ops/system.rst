:mod:`ops.system` --- Provides high-level control over the production system
============================================================================

.. automodule:: ops.system


The :class:`ProductionSystem` Class
-----------------------------------
.. autoclass:: ProductionSystem()

General Attributes
""""""""""""""""""
.. automethod:: ProductionSystem.__init__
.. autoattribute:: ProductionSystem.mediator

Locking
"""""""
.. autoattribute:: ProductionSystem.isLocked
.. automethod:: ProductionSystem.lock
.. automethod:: ProductionSystem.unlock

Calibration
"""""""""""
.. autoattribute:: ProductionSystem.isCalibrated
.. autoattribute:: ProductionSystem.isBeingCalibrated
.. autoattribute:: ProductionSystem.calibrationData
.. autoattribute:: ProductionSystem.calibrationManager
.. automethod:: ProductionSystem.startCalibration
.. automethod:: ProductionSystem.abortCalibration

.. seealso::
    :meth:`~ProductionSystem.performMagicCalibration`

Monitoring
""""""""""
.. autoattribute:: ProductionSystem.isInSafeMode
.. autoattribute:: ProductionSystem.monitorInterval
.. autoattribute:: ProductionSystem.maxSafeTemperature
.. autoattribute:: ProductionSystem.maxSafeTemperatureSensorVoltage
.. autoattribute:: ProductionSystem.heatingCurrentInSafeMode
.. automethod:: ProductionSystem.enterSafeMode

Heating
"""""""
.. autoattribute:: ProductionSystem.heatingCurrent
.. autoattribute:: ProductionSystem.heatingCurrentWhileIdle
.. autoattribute:: ProductionSystem.maxHeatingCurrent
.. autoattribute:: ProductionSystem.temperatureSensorVoltage
.. autoattribute:: ProductionSystem.temperature
.. autoattribute:: ProductionSystem.targetTemperature
.. autoattribute:: ProductionSystem.minTargetTemperature
.. autoattribute:: ProductionSystem.maxTargetTemperature
.. automethod:: ProductionSystem.isValidTargetTemperature
.. automethod:: ProductionSystem.startHeatingWithCurrent
.. automethod:: ProductionSystem.startHeatingToTemperature
.. automethod:: ProductionSystem.idle

Heater Movement
"""""""""""""""
.. autoattribute:: ProductionSystem.heaterPosition
.. autoattribute:: ProductionSystem.heaterTargetPosition
.. automethod:: ProductionSystem.startHeaterMovement

Testing
"""""""
.. autoattribute:: ProductionSystem.isSimulation
.. autoattribute:: ProductionSystem.speedFactor
.. automethod:: ProductionSystem.performMagicCalibration
