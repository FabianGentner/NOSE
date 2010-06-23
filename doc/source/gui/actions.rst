:mod:`gui.actions`
******************

.. automodule:: gui.actions


Functions
=========

.. autofunction:: createActionGroup
.. autofunction:: _makeMenuAction


Error Messages
==============

.. autodata:: NOT_CALIBRATED_ERROR_MESSAGE
.. autodata:: NO_CALIBRATION_DATA_ERROR_MESSAGE
.. autodata:: NO_SIMULATION_ERROR_MESSAGE


:class:`NoseAction`
===================

.. autoclass:: NoseAction

    |

    **Class Attributes**

    .. autoattribute:: name
    .. autoattribute:: text
    .. autoattribute:: stock
    .. autoattribute:: accelerator
    .. autoattribute:: radioGroupName
    .. autoattribute:: radioValue
    .. autoattribute:: radioActive
    .. autoattribute:: requiresCalibrationData
    .. autoattribute:: requiresSimulation

    |

    **Instance Methods**

    .. automethod:: __init__
    .. automethod:: activate
    .. automethod:: run
    .. automethod:: _handleCalibrationDataChange


The Actual Actions
==================

.. autoclass:: QuitAction
.. autoclass:: ShowCalibrationDialogAction
.. autoclass:: LoadCalibrationDataAction
.. autoclass:: SaveCalibrationDataAction
.. autoclass:: SaveCalibrationDataAsAction
.. autoclass:: ClearCalibrationDataAction

