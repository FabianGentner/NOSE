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

import numpy
import time
import unittest

from test import *

import ops.calibration.leastsquare as ls
import util


class LeastSquareModuleTests(unittest.TestCase):
    """
    Tests for the functions in the :mod:`~ops.calibration.leastsquare` module.
    """

    PARAMETERS = (
        'startingTemperatureStartingEstimate',
        'finalTemperatureStartingEstimateFactor',
        'tauStartingEstimate',
        'coefficientsStartingEstimate')

    NEW_VALUES = (100.0, 10.0, 1.0, tuple('dummy'))


    def setUp(self):
        self.oldValues = tuple(getattr(ls, p) for p in self.PARAMETERS)
        for p, v in zip(self.PARAMETERS, self.NEW_VALUES):
            setattr(ls, p, v)


    def tearDown(self):
        for p, v, in zip(self.PARAMETERS, self.oldValues):
            setattr(ls, p, v)


    def testGetFirstStartingEstimates(self):
        """Tests the :func:`getFirstStartingEstimates` function."""
        solution = ls.getFirstStartingEstimates(8.0)
        self.assertEqual(solution.startingTemperature, 100.0)
        self.assertEqual(solution.finalTemperature, 80.0)
        self.assertEqual(solution.tau, 1.0)
        self.assertEqual(solution.coefficients, tuple('dummy'))


    def testGetSubsequentStartingEstimates(self):
        """Tests the :func:`getSubsequentStartingEstimates` function."""
        prev = ls.Solution(-10.0, 100.0, 5.0, tuple('DUMMY'))
        solution = ls.getSubsequentStartingEstimates(200.0, prev, 3.0)
        self.assertEqual(solution.startingTemperature, 200.0)
        self.assertEqual(solution.finalTemperature, 230.0)
        self.assertEqual(solution.tau, 5.0)
        self.assertEqual(solution.coefficients, tuple('DUMMY'))


    def testFlattenSolution(self):
        """Tests the :func:`_flattenSolution` function."""
        solution = ls.Solution(25.0, 125.0, 15.0, tuple('dummy'))
        self.assertEqual(ls._flattenSolution(solution),
            (25.0, 125.0, 15.0, 'd', 'u', 'm', 'm', 'y'))


    def testVoltagesFromTemperatures(self):
        """Tests the :func:`_voltagesFromTemperatures` function."""
        temperatures = numpy.asarray([55.0, 100.0])
        parameters = (0.0001, -0.001, 0.01, -0.1, 1.0)
        voltages = ls._voltagesFromTemperatures(temperatures, *parameters)
        self.assertEqual(list(voltages), [774.4375, 9091.0])


    def testTemperaturesFromTimes(self):
        """Tests the :func:`_temperaturesFromTimes` function."""
        times = numpy.asarray([-numpy.log(0.99), -numpy.log(0.9)]) * 5.0
        temperatures = ls._temperaturesFromTimes(times, 50.0, 550.0, 5.0)
        self.assertAlmostEqual(temperatures[0], 55.0)
        self.assertAlmostEqual(temperatures[1], 100.0)


    def testVoltagesFromTimes(self):
        """Tests the :func:`_voltagesFromTimes` function."""
        times = numpy.asarray([-numpy.log(0.99), -numpy.log(0.9)]) * 5.0
        voltages = ls._voltagesFromTimes(
            times, 50.0, 550.0, 5.0, 0.0001, -0.001, 0.01, -0.1, 1.0)
        self.assertAlmostEqual(voltages[0], 774.4375)
        self.assertAlmostEqual(voltages[1], 9091.0)


    def testErrorFunction(self):
        """Tests the :func:`_errorFunction`."""
        parameters = (50.0, 550.0, 5.0, 0.0001, -0.001, 0.01, -0.1, 1.0)
        times = numpy.asarray([-numpy.log(0.99), -numpy.log(0.9)]) * 5.0
        voltages = numpy.asarray([775.4375, 9090.0])
        error = ls._errorFunction(parameters, times, voltages)
        self.assertAlmostEqual(error[0], 1.0)
        self.assertAlmostEqual(error[1], -1.0)



class LeastSquareThradTests(unittest.TestCase):
    """Tests the :class:`LeastSquareThread` class."""

    def setUp(self):
        self.coeffs = (0.0001, -0.001, 0.01, -0.1, 1.0)
        self.startingEstimations = ls.Solution(5.0, 150.0, 5.0, self.coeffs)
        self.thread = ls.LeastSquareThread(self.startingEstimations)

        #self.sleepLogger = wrapLogger(time.sleep)


    def tearDown(self):
        self.thread.stop()
        #self.sleepLogger.unwrap()


    def testReadOnly(self):
        """Checks that read-only properties are actually read-only."""
        for p in ('solution', 'solutionsFound'):
            self.assertRaises(AttributeError, setattr, self.thread, p, None)


    def testRefreshData(self):
        """Tests the :meth:`refreshData` method."""
        times = [0.1, 0.2, 0.3]
        voltages = [0.4, 0.45, 0.5]
        self.thread.voltagesRequired = 3

        self.thread.refreshData(times=times[:2], voltages=voltages[:2])
        self.assertEqual(self.thread._data, None)

        self.thread.refreshData(times=times, voltages=voltages)
        self.assertTrue(all(self.thread._data[0] == times))
        self.assertTrue(all(self.thread._data[1] == voltages))

        self.assertRaises(util.ApplicationError, self.thread.refreshData,
            times=times, voltages=voltages[:2])


    def testStart(self):
        """Tests the :meth:`start` method."""
        logger = wrapLogger(self.thread.run)
        self.thread.start()
        self.assertTrue(self.thread.isAlive())
        self.assertEqual(logger.log, [()])


    #def testRun(self):
        #"""Tests the :meth:`run` method."""
        #self.thread.sleepInterval = 0.1
        #findSolutionlogger = replaceWithLogger(self.thread._findSolution)

        #self.thread.run()
        #self.assertEqual(findSolutionLogger.log, [()])
        #self.assertEqual(self.sleepLogger.log, [(0.1)])






