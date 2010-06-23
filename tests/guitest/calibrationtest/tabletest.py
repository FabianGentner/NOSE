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

from gui.calibration.table import *
from ops.calibration.data import CalibrationData
from test import *

import gui.mediator
import ops.system


class MeasurementTableTests(unittest.TestCase):
    """
    Tests for the :mod:`~gui.calibration.table` module.
    """

    def setUp(self):
        self.mediator = gui.mediator.Mediator()
        self.system = ops.system.ProductionSystem(self.mediator)
        self.handler = MeasurementTableHandler(self.system)
        self.cd = makeCalibrationData()
        self.system.calibrationData = self.cd


    def testCreateMeasurementTable(self):
        """Tests the :func:`createMeasurementTable` function."""
        widget = createMeasurementTable(self.system)
        self.assertNotEqual(widget, None)


    def testWidget(self):
        """Tests the :attr:`widget` property."""
        self.assertEqual(self.handler.widget, self.handler._treeView)
        self.assertRaises(AttributeError, setattr, self.handler, 'widget', 0)


    def testEvents(self):
        """Check that the class responds to events."""
        logger = wrapLogger(self.handler._updateTable)
        self.system.calibrationData = CalibrationData()
        self.assertEqual(logger.log, [self.system.calibrationData])


    def testRowCount(self):
        """Checks that the table has the expected number of rows."""
        rowCount = self.handler.widget.get_model().iter_n_children

        self.assertEqual(rowCount(None), len(self.cd.measurements))

        self.system.calibrationData = CalibrationData()
        self.assertEqual(rowCount(None), 0)

        self.system.calibrationData = self.cd
        self.assertEqual(rowCount(None), len(self.cd.measurements))


    def testButtonPressed(self):
        """Tests the :meth:`_buttonPressed` method."""
        method = self.handler._buttonPressed
        logger = replaceWithLogger(self.handler._showPopupMenu)

        self.assertFalse(method('dummy', Stub(None, button=1)))
        self.assertEqual(logger.log, [])

        self.assertFalse(method('dummy', Stub(None, button=2)))
        self.assertEqual(logger.log, [])

        stub = Stub(None, button=3, time=1000)
        self.assertTrue(method('dummy', stub))
        self.assertEqual(logger.log, [stub])


    def testShowPopupMenu(self):
        """Tests the :meth:`_showPopupMenu` method."""

        # No rows are selected; the menu items should be insensitive.
        menu = self.handler._showPopupMenu(Stub(None, button=3, time=1000))
        for child in menu.get_children():
            self.assertFalse(child.get_property('sensitive'))

        # Select a row. The menu items should be sensitive.
        self.handler.widget.get_selection().select_path((2,))
        menu = self.handler._showPopupMenu(Stub(None, button=3, time=1001))
        for child in menu.get_children():
            self.assertTrue(child.get_property('sensitive'))

        # Lock the system. The menu items should be insensitive.
        self.system.lock(23)
        menu = self.handler._showPopupMenu(Stub(None, button=3, time=1002))
        for child in menu.get_children():
            self.assertFalse(child.get_property('sensitive'))


    def testRetakeSelectedMeasurementsActivated(self):
        """Tests the :meth:`_retakeSelectedMeasurementsActivated` method."""
        logger = replaceWithLogger(self.system.startCalibration)
        self.handler._retakeSelectedMeasurementsActivated('dummy', (3.0, 5.0))
        self.assertEqual(logger.log, [(3.0, 5.0)])


    def testDeleteSelectedMeasurementsActivated(self):
        """Tests the :meth:`_deleteSelectedMeasurementsActivated` method."""
        # NOTE: Uses knowledge about makeCalibrationData's behavior.
        self.handler._deleteSelectedMeasurementsActivated(
            'dummy', (2.0, 8.0, 10.0, 16.0, 20.0))
        self.assertEqual(self.cd.heatingCurrents, (4.0, 6.0, 12.0, 14.0, 18.0))


    def testCurrentsFromRows(self):
        """Tests the :meth:`_currentsFromRows` method."""
        # NOTE: Uses knowledge about makeCalibrationData's behavior.
        currents = self.handler._currentsFromRows((0, 3, 4, 7, 9))
        self.assertEqual(currents, (2.0, 8.0, 10.0, 16.0, 20.0))

