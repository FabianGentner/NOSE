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

import unittest

from test import *
from ops.calibration.data import CalibrationData

import gui.calibration.charts
import gui.mediator
import ops.calibration.event
import ops.system


class ChartHandlerTests(unittest.TestCase):
    """
    Tests for the :class:`~gui.calibration.charts.ChartHandler` class.
    """

    def setUp(self):
        self.mediator = gui.mediator.Mediator()
        self.system = ops.system.ProductionSystem(self.mediator)
        self.handler = gui.calibration.charts.ChartHandler(self.system)


    def testWidgets(self):
        """Tests the widget properties."""
        for n in ('measurementsChart', 'temperatureChart', 'currentChart'):
            self.assertNotEqual(getattr(self.handler, n), None)
            self.assertRaises(AttributeError, setattr, self.handler, n, None)


    def testEvents(self):
        """Check that the class responds to events."""
        logger = wrapLogger(self.handler._updateGraphs)
        self.mediator.noteEvent(ops.calibration.event.CalibrationDataChanged(
            self.system, self.system.calibrationData))
        self.assertEqual(logger.log, [self.system.calibrationData])


    def testEmptyCalibrationData(self):
        """Tests updating with an empty calibration data object."""
        self.handler._updateGraphs(CalibrationData())
        self.assertEqual(self.handler.measurementsChart._graphs, [])
        self.assertEqual(self.handler.temperatureChart._graphs, [])
        self.assertEqual(self.handler.currentChart._graphs, [])


    def testIncompleteCalibrationData(self):
        """Tests updating with an incomplete calibration data object."""
        cd = CalibrationData()
        cd.addMeasurement(1.0, 2.0, 3.0)
        cd.addMeasurement(2.0, 3.0, 4.0)
        cd.addMeasurement(3.0, 4.0, 5.0)
        self.handler._updateGraphs(cd)
        self.assertEqual(len(self.handler.measurementsChart._graphs), 2)
        self.assertEqual(len(self.handler.temperatureChart._graphs), 1)
        self.assertEqual(len(self.handler.currentChart._graphs), 1)


    def testFullCalibrationData(self):
        """Tests updating with a complete calibration data object."""
        self.handler._updateGraphs(makeCalibrationData())
        self.assertEqual(len(self.handler.measurementsChart._graphs), 3)
        self.assertEqual(len(self.handler.temperatureChart._graphs), 2)
        self.assertEqual(len(self.handler.currentChart._graphs), 2)

