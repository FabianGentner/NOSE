:mod:`ops.calibration.leastsquare` --- Estimates the heating parameters
=======================================================================

.. automodule:: ops.calibration.leastsquare

The :class:`LeastSquareThread` Class
------------------------------------
.. autoclass:: LeastSquareThread
.. autoattribute:: LeastSquareThread.solution
.. autoattribute:: LeastSquareThread.solutionsFound
.. automethod:: LeastSquareThread.refreshData
.. automethod:: LeastSquareThread.start
.. automethod:: LeastSquareThread.stop
.. autoattribute:: LeastSquareThread.voltagesRequired
.. autoattribute:: LeastSquareThread.sleepInterval

The :class:`Solution` Named Tuple
---------------------------------
.. autoclass:: Solution

Starting Estimates
------------------
.. autofunction:: getFirstStartingEstimates
.. autofunction:: getSubsequentStartingEstimates
.. autodata:: startingTemperatureStartingEstimate
.. autodata:: finalTemperatureStartingEstimateFactor
.. autodata:: tauStartingEstimate
.. autodata:: coefficientsStartingEstimate