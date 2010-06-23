:mod:`ops.calibration.manager` --- Runs the calibration procedure
=================================================================

.. automodule:: ops.calibration.manager

The :class:`CalibrationManager` Class
-------------------------------------
.. autoclass:: CalibrationManager
.. autoattribute:: CalibrationManager.system
.. autoattribute:: CalibrationManager.currents
.. automethod:: CalibrationManager.startCalibration
.. automethod:: CalibrationManager.abortCalibration

Parameters
""""""""""
.. autoattribute:: CalibrationManager.precision
.. autoattribute:: CalibrationManager.tickInterval

Progress Information
""""""""""""""""""""
.. autoattribute:: CalibrationManager.isRunning
.. autoattribute:: CalibrationManager.state
.. autoattribute:: CalibrationManager.hasMoreHeatingStages
.. autoattribute:: CalibrationManager.heatingStageIndex
.. autoattribute:: CalibrationManager.heatingStageCount
.. autoattribute:: CalibrationManager.remainingHeatingStageCount
.. automethod:: CalibrationManager.getProgress
.. automethod:: CalibrationManager.getExtendedProgress

Calibration States
------------------
.. autodata:: STATE_NOT_YET_STARTED
.. autodata:: STATE_MOVING_HEATER
.. autodata:: STATE_HEATING
.. autodata:: STATE_WAITING_FOR_TEMPERATURE
.. autodata:: STATE_DONE

Status Codes
------------
.. autodata:: STATUS_ABORTED
.. autodata:: STATUS_SAFE_MODE_TRIGGERED
.. autodata:: STATUS_INVALID_CURRENT
.. autodata:: STATUS_FINISHED

