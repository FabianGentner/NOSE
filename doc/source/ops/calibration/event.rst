:mod:`ops.calibration.event` --- Contains calibration-related event classes
===========================================================================

.. automodule:: ops.calibration.event

The :class:`CalibrationStarted` Class
-------------------------------------
.. autoclass:: CalibrationStarted()
.. autoattribute:: CalibrationStarted.system
.. autoattribute:: CalibrationStarted.manager

The :class:`CalibrationOver` Class
----------------------------------
.. autoclass:: CalibrationOver()
.. autoattribute:: CalibrationOver.system
.. autoattribute:: CalibrationOver.manager
.. autoattribute:: CalibrationOver.status
.. autoattribute:: CalibrationOver.unusedCurrents

The :class:`TemperatureRequested` Class
---------------------------------------
.. autoclass:: TemperatureRequested()
.. autoattribute:: TemperatureRequested.manager
.. autoattribute:: TemperatureRequested.system
.. autoattribute:: TemperatureRequested.callback

The :class:`TemperatureRequestOver` Class
-----------------------------------------
.. autoclass:: TemperatureRequestOver()
.. autoattribute:: TemperatureRequestOver.manager
.. autoattribute:: TemperatureRequestOver.system

The :class:`CalibrationDataChanged` Class
-----------------------------------------
.. autoclass:: CalibrationDataChanged()
.. autoattribute:: CalibrationDataChanged.system
.. autoattribute:: CalibrationDataChanged.calibrationData
