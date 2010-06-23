# -*- coding: utf-8 -*-

# Copyright (c) 2010 Institute for High-Frequency Technology, Technical
# University of Braunschweig
#
# This file is part of NOSE.
#
# NOSE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# NOSE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NOSE. If not, see <http://www.gnu.org/licenses/>.

"""
This module estimates a set of parameters that describe the development of the
:term:`heating temperature` over time for a given :term:`heating current`, and
the :term:`temperature sensor voltage` for a given temperature. The results
are then used by the :class:`~ops.calibration.manager.CalibrationManager` to
estimate the progress of a heating stage, and to determine whether the heating
temperature is close enough to its final value for a :term:`temperature
measurement` to be taken.

The module assumes that the heating temperature :math:`T` at time :math:`t` is

.. math::

    T = T_0 + (T_1 - T_0) \\times (1 - e^{-t/\\tau}),

and that the temperature sensor voltage :math:`U` for that temperature is

.. math::

    U = a_4 T^4 + a_3 T^3 + a_2 T^2 + a_1 T + a_0,

where :math:`T_0` is the temperature at the beginning of the heating stage,
:math:`T_1` is the final temperature for the heating current used, and
:math:`\\tau` and :math:`a_4, \\dots, a_0` are constants.

The module then estimates :math:`T_0, T_1, \\tau,` and the coefficients
:math:`a_4, \\dots, a_0` using :func:`scipy.optimize.leastsq`.

The minimization is performed in a worker thread (:class:`LeastSquareThread`)
since it may take up to half a second, and would otherwise render the
application unresponsive.
"""

import collections
import numpy
import scipy.optimize
import time
import threading

import util


###############################################################################
# THE LEAST SQUARE THREAD CLASS                                               #
###############################################################################

class LeastSquareThread(threading.Thread):
    """
    Creates a new instance of this class. `startingEstimates` must be a
    :class:`Solution` object that is usable as the starting point of
    the minimzation. Suitable :class:`Solution`\\s can be optained from
    :func:`getFirstStartingEstimates` or
    :func:`getSubsequentStartingEstimates`.
    """

    def __init__(self, startingEstimates):
        super(self.__class__, self).__init__()
        self.setDaemon(True)

        self._startingEstimates = startingEstimates
        self._data = None
        self._solution = None

        self._solutionsFound = 0
        self._done = False


    @property
    def solution(self):
        """
        The most recent solution of the minimization, as a :class:`Solution`
        object, or ``None`` if a solution has not yet been found. Read-only.
        """
        return self._solution


    @property
    def solutionsFound(self):
        """
        The number of solutions the thread has found so far. Read-only.
        """
        return self._solutionsFound


    def refreshData(self, times, voltages):
        """
        Updates the data the minimization is based on. The arguments are
        a sequences of times (measured from the start of the heating stage)
        and a sequence of the temperature sensor voltages at these times,
        which must have the same length.

        This method can be safely called from the main thread. The sequences
        are copied before the method returns.
        """
        if len(times) != len(voltages):
            raise util.ApplicationError('the sequences have different lengths')
        if len(voltages) >= self.voltagesRequired:
            # Assigning each argument to its own instance attribute would
            # create a race condition, which might cause your computer to
            # explode. Don't do it!
            self._data = (numpy.asarray(times), numpy.asarray(voltages))


    def start(self):
        """
        Starts the thread. A thread that has been stopped cannot be restarted.
        """
        super(self.__class__, self).start()


    def run(self):
        """
        Tries to find solutions given the most recent data, until the thread
        is stopped, sleeping for :attr:`sleepInterval` seconds after each
        attempt.

        .. note::

            To start the thread, call :meth:`start`, not :meth:`run`.
            This method should only be called by :meth:`Thread.start`.
        """
        while not self._done:
            self._findSolution()
            time.sleep(self.sleepInterval)


    def _findSolution(self):
        """
        Does the actual work.
        """
        if self.solution == None:
            start = _flattenSolution(self._startingEstimates)
        else:
            start = _flattenSolution(self.solution)

        if self._data != None:
            # ISSUE: The parameter `warning` is deprecated in favor of using
            #        the warnings module, but that does not actually work.
            result, status = scipy.optimize.leastsq(
                _errorFunction, start, args=self._data, warning=False)

            if status in (1, 2, 3, 4):
                # 1, 2, 3, and 4 are magic numbers that indicate that `result`
                # actually contains a solution, not just random garbage.
                # Searching the Internet for "minpack lmder" should reveal the
                # subtle and largely incomprehensible differences in meaning
                # between these numbers.
                self._solution = Solution(
                    startingTemperature=result[0],
                    finalTemperature=result[1],
                    tau=result[2],
                    coefficients=tuple(result[3:]))

                self._solutionsFound += 1


    def stop(self):
        """
        Stops the thread. It may take some time for the thread to actually
        terminate, and one last solution may be produced.
        """
        self._done = True


    #: The smallest number of reported temperature sensor voltages great
    #: enough to perform a useful estimation. If fewer voltages are
    #: passed to :meth:`refreshData`, they are ignored.
    #:
    #: This is a class attribute, but it can be set on an instance to
    #: override the default value. If the value is set too low, an
    #: exception may be raised during minimization.
    voltagesRequired = 12
    # TODO: What kind of exception?
    # TODO: Gracefully handle exceptions caused by this being too low?


    #: The amount of time the thread sleeps after it finds a solution or fails
    #: to find one, in seconds. This is a class attribute, but it can be set
    #: on an instance to override the default value (even after :meth:`start`
    #: has been called).
    sleepInterval = 1.0


###############################################################################
# SOLUTION                                                                    #
###############################################################################

#: A named tuple that contains the solution of a minimzation, or the starting
#: estimates for one. The items in this tuple are `startingTemperature`,
#: `finalTemperature`, `tau`, and `coefficients`, where the first three are
#: :math:`T_0, T_1,` and :math:`\tau` as defined above, and the last is an
#: unnamed tuple containing :math:`a_4, \dots, a_0,` in that order.
Solution = collections.namedtuple('Solution',
    'startingTemperature, finalTemperature, tau, coefficients')


###############################################################################
# STARTING ESTIMATES                                                          #
###############################################################################

def getFirstStartingEstimates(current):
    """
    Creates a :class:`Solution` that contains suitable values for it to be
    usable as the as the starting point of the minimzation in the first
    heating stage of the calibration procedure. `current` is the heating
    current used for that stage.
    """
    return Solution(
        startingTemperature=startingTemperatureStartingEstimate,
        finalTemperature=(current * finalTemperatureStartingEstimateFactor),
        tau=tauStartingEstimate,
        coefficients=coefficientsStartingEstimate)


def getSubsequentStartingEstimates(
    previousTemperature, previousSolution, extraCurrent):
    """
    Creates a :class:`Solution` that contains suitable values for it to be
    usable as the as the starting point of the minimzation in a heating stage
    other than the first. `previousTemperature` is the heating temperature
    measured at the end of the previous heating stage, `previousSolution`
    is the solution of the minimization performed in the previous heating
    stage, and `extraCurrent` is the heating current in the new heating
    stage minus the heating current in the previous heating stage.
    """
    extraTemperature = extraCurrent * finalTemperatureStartingEstimateFactor
    return Solution(
        startingTemperature=previousTemperature,
        finalTemperature=(previousTemperature + extraTemperature),
        tau=previousSolution.tau,
        coefficients=previousSolution.coefficients)


#: A suitable starting estimate for the starting temperature.
#: Used by :func:`getFirstStartingEstimates`
startingTemperatureStartingEstimate = 20.0

#: A factor by which the heating current used in a heating stage can be
#: multiplied in order to get a suitable starting estimate for the final
#: temperature in that stage. Used by :func:`getFirstStartingEstimates`
#: and :func:`getSubsequentStartingEstimates`.
finalTemperatureStartingEstimateFactor = 75.0

#: A suitable starting estimate for tau.
#: Used by :func:`getFirstStartingEstimates`.
tauStartingEstimate = 100.0

#: A tuple that contains suitable starting estimates for the coefficients.
#: Used by :func:`getFirstStartingEstimates`
coefficientsStartingEstimate = (0.001, -0.01, 0.1, -1.0, 0.0)


def _flattenSolution(solution):
    """
    Flattens a :class:`Solution` tuple. That is, the nested tuples
    ``(startingTemperature, finalTemperature, tau, (a4, a3, a2, a1, a0))``
    are turned into a single tuple
    ``(startingTemperature, finalTemperature, tau, a4, a3, a2, a1, a0)``.
    """
    return solution[0:3] + solution[3]


###############################################################################
# THE ERROR FUNCTION                                                          #
###############################################################################

def _errorFunction(p, times, voltages):
    """
    The error function used by the minimzation.
    """
    return voltages - _voltagesFromTimes(times, *p)


def _voltagesFromTimes(times, T0, T1, tau, a4, a3, a2, a1, a0):
    """
    Returns the voltages at the given times, for the given parameters.
    """
    temperatures = _temperaturesFromTimes(times, T0, T1, tau)
    return _voltagesFromTemperatures(temperatures, a4, a3, a2, a1, a0)


def _temperaturesFromTimes(times, T0, T1, tau):
    """
    Returns the temperatures at the given times, for the given parameters.
    """
    return T0 + (T1 - T0) * (1 - numpy.exp(-times / tau))


def _voltagesFromTemperatures(temperatures, a4, a3, a2, a1, a0):
    """
    Returns the voltages for the given temperatures, using the given
    parameters.
    """
    T = temperatures
    return a4 * T**4 + a3 * T**3 + a2 * T**2 + a1 * T + a0
