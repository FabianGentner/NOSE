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

import math
import numpy
import time
import unittest

import ops.error
import ops.simulation
import test


class SimulatedDeviceInterfaceTests(unittest.TestCase):
    """Tests for :class:`ops.simulation.SimulatedDeviceInterface`."""

    def setUp(self):
        self.simulation = ops.simulation.SimulatedDeviceInterface()

        self.simulation.finalTemperatureFromCurrent = numpy.poly1d([10.0, 0.0])
        self.simulation.voltageFromTemperature = numpy.poly1d([0.0001, 0.0])
        self.simulation.tau = 20.0
        self.simulation.heaterMovementRate = 0.3

        ops.simulation.time = self.fakeTime = test.FakeTime(*([0.0] * 100))


    def tearDown(self):
        ops.simulation.time = time


    ###########################################################################
    # HEATING                                                                 #
    ###########################################################################

    def testHeatingFunctionality(self):
        """
        Tests the functionality associated with heating:
        :attr:`heatingCurrent`, :attr:`temperatureSensorVoltage`,
        :attr:`temperature`, and :meth:`startHeatingWithCurrent`.
        """
        sim = self.simulation
        currents = (2.0, 4.0, 2.0, 2.0, 8.0, 0.0, 6.0)

        self.fakeTime.times = ([0.0] * 3
            + sorted([15.0 * n for n in xrange(1, len(currents))] * 3)
            + [15.0 * len(currents)] * 2)
        xT = 0.0

        self.assertEqual(sim.heatingCurrent, 0.0)
        self.assertEqual(sim.temperature, 0.0)
        self.assertEqual(sim.temperatureSensorVoltage, 0.0)

        for current in currents:
            sim.startHeatingWithCurrent(current)

            xT = xT + (10.0 * current - xT) * (1.0 - math.exp(-15.0 / 20.0))
            self.assertEqual(sim.heatingCurrent, current)
            self.assertEqual(xT, sim.temperature)
            self.assertEqual(xT * 0.0001, sim.temperatureSensorVoltage)


    def testHeatingErrors(self):
        """Tries a number of illegal operations related to heating."""
        self.assertRaises(ops.error.InvalidHeatingCurrentError,
            self.simulation.startHeatingWithCurrent, -10.0)

        self.assertRaises(AttributeError,
            setattr, self.simulation, 'heatingCurrent', 2.0)
        self.assertRaises(AttributeError,
            setattr, self.simulation, 'temperature', 100.0)
        self.assertRaises(AttributeError,
            setattr, self.simulation, 'temperatureSensorVoltage', 0.1)


    ###########################################################################
    # HEATER MOVEMENT                                                         #
    ###########################################################################

    def testHeaterMovementFunctionality(self):
        """
        Tests the functionality associated with heater movement:
        :attr:`heaterPosition`, :attr:`heaterTargetPosition`,
        and :meth:`startHeaterMovement`.
        """
        sim = self.simulation

        self.fakeTime.times = [0.0, 0.0, 1.0, 2.0, 3.0]
        sim.startHeaterMovement(0.8)
        self.assertAlmostEqual(sim.heaterTargetPosition, 0.8)
        self.assertAlmostEqual(sim.heaterPosition, 0.0)
        self.assertAlmostEqual(sim.heaterPosition, 0.3)
        self.assertAlmostEqual(sim.heaterPosition, 0.6)
        self.assertAlmostEqual(sim.heaterPosition, 0.8)

        self.fakeTime.times = [5.0, 5.0, 6.0, 7.0]
        sim.startHeaterMovement(0.3)
        self.assertAlmostEqual(sim.heaterTargetPosition, 0.3)
        self.assertAlmostEqual(sim.heaterPosition, 0.8)
        self.assertAlmostEqual(sim.heaterPosition, 0.5)
        self.assertAlmostEqual(sim.heaterPosition, 0.3)

        self.fakeTime.times = [
            10.0, 10.0, 11.0, 12.0, 12.0, 12.0, 13.0, 13.0, 13.0, 14.0, 15.0]
        sim.startHeaterMovement(1.0)
        self.assertAlmostEqual(sim.heaterPosition, 0.3)
        self.assertAlmostEqual(sim.heaterPosition, 0.6)
        self.assertAlmostEqual(sim.heaterPosition, 0.9)
        sim.startHeaterMovement(0.0)
        self.assertAlmostEqual(sim.heaterPosition, 0.9)
        self.assertAlmostEqual(sim.heaterPosition, 0.6)
        sim.startHeaterMovement(0.0)
        self.assertAlmostEqual(sim.heaterPosition, 0.6)
        self.assertAlmostEqual(sim.heaterPosition, 0.3)
        self.assertAlmostEqual(sim.heaterPosition, 0.0)


    def testHeaterMovementErrors(self):
        """
        Tries a number of illegal operation related to heater movement.
        """
        self.assertRaises(ops.error.InvalidHeaterPositionError,
            self.simulation.startHeaterMovement, -0.1)
        self.assertRaises(ops.error.InvalidHeaterPositionError,
            self.simulation.startHeaterMovement, 1.1)

        self.assertRaises(AttributeError,
            setattr, self.simulation, 'heaterPosition', 0.5)
        self.assertRaises(AttributeError,
            setattr, self.simulation, 'heaterTargetPosition', 0.5)


    ###########################################################################
    # TESTING                                                                 #
    ###########################################################################

    def testIsSimulation(self):
        """Tests the :attr:`isSimulation` property."""
        self.assertTrue(self.simulation.isSimulation)
        self.assertRaises(AttributeError,
            setattr, self.simulation, 'isSimulation', False)


    def testSpeedFactorWithHeating(self):
        """Tests the :attr:`speedFactor`'s effect on heating."""
        sim = self.simulation
        self.fakeTime.times = [0.0, 15.0, 15.0, 30.0, 30.0, 45.0]

        sim.startHeatingWithCurrent(6.0)
        xT = 60.0 * (1.0 - math.exp(-15.0 / 20.0))
        self.assertEqual(sim.temperature, xT)
        sim.speedFactor = 2.0
        xT = xT + (60.0 - xT) * (1.0 - math.exp(-30.0 / 20.0))
        self.assertEqual(sim.temperature, xT)
        sim.speedFactor = 0.5
        xT = xT + (60.0 - xT) * (1.0 - math.exp(-7.5 / 20.0))
        self.assertEqual(sim.temperature, xT)


    def testSpeedFactorWithHeaterMovement(self):
        """Tests the :attr:`speedFactor`'s effect on heater movement."""
        sim = self.simulation
        self.fakeTime.times = [0.0, 0.5, 0.5, 1.0, 1.0, 2.0]

        sim.startHeaterMovement(1.0)
        self.assertAlmostEqual(sim.heaterPosition, 0.15)
        sim.speedFactor = 2.0
        self.assertAlmostEqual(sim.heaterPosition, 0.45)
        sim.speedFactor = 0.5
        self.assertAlmostEqual(sim.heaterPosition, 0.6)


    def testInvalidSpeedFactor(self):
        """Tests setting :attr:`speedFactor` to an invalid value."""
        self.assertRaises(ValueError,
            setattr, self.simulation, 'speedFactor', -1.0)

