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

import gc
import gtk
import unittest
import weakref

import gui.main
import ops.system


class AllTests(unittest.TestCase):
    """
    Tests for the gui.main module.
    """

    def setUp(self):
        self.system = ops.system.ProductionSystem()
        self.handler = gui.main.MainWindowHandler(self.system)


    def testGC(self):
        """Make sure the class is properly garbage-collected."""
        wr = weakref.ref(self.handler)
        self.handler = None
        gc.collect()
        self.assertEqual(wr(), None)


    def testGetPreferredSize(self):
        """Tests the _getPreferredSize method."""
        gui.main.MAIN_WINDOW_MAX_SCREEN_FRACTION = 0.5
        gui.main.MAIN_WINDOW_SIZE = (1000, 800)
        size = self.handler._getPreferredSize(FakeScreen([(2400, 1800)]))
        self.assertEqual(size, (1000, 800))
        size = self.handler._getPreferredSize(FakeScreen([(1800, 1200)]))
        self.assertEqual(size, (900, 600))
        monitors = [(3000, 2000), (800, 600), (1500, 1000)]
        size = self.handler._getPreferredSize(FakeScreen(monitors))
        self.assertEqual(size, (400, 300))


    def testShowCalibrationDialog(self):
        """Tests the showCalibrationDialog method."""
        self.handler.showCalibrationDialog()
        cdh = self.handler._calibrationDialogHandler
        self.assertNotEqual(cdh, None)
        cdh._close()
        self.handler.showCalibrationDialog()
        self.assertEqual(cdh, self.handler._calibrationDialogHandler)


    def testUpdateStatusBar(self):
        """Tests the _updateStatusBar method."""
        fakeSystem = FakeSystem()
        self.handler._system = fakeSystem
        self.handler._updateStatusBar()
        self.assertEqual(self.handler._temperatureLabel.get_text(), '0 V')
        fakeSystem.temperatureSensorVoltage = 12.345
        self.handler._updateStatusBar()
        self.assertEqual(self.handler._temperatureLabel.get_text(), '12.345 V')
        fakeSystem.temperatureSensorVoltage = 1.234567
        self.handler._updateStatusBar()
        self.assertEqual(self.handler._temperatureLabel.get_text(), '1.2346 V')
        fakeSystem.temperature = 0
        self.handler._updateStatusBar()
        self.assertEqual(self.handler._temperatureLabel.get_text(), '0 °C')
        fakeSystem.temperature = 1000
        self.handler._updateStatusBar()
        self.assertEqual(self.handler._temperatureLabel.get_text(), '1000 °C')
        fakeSystem.temperature = 1234.56
        self.handler._updateStatusBar()
        self.assertEqual(self.handler._temperatureLabel.get_text(), '1234 °C')


class FakeScreen(object):
    def __init__(self, monitors):
        self.monitors = monitors

    def get_n_monitors(self):
        return len(self.monitors)

    def get_monitor_geometry(self, n):
        return gtk.gdk.Rectangle(0, 0, *self.monitors[n])


class FakeSystem(object):
    temperature = None
    temperatureSensorVoltage = 0.0
