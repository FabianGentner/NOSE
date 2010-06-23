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

from gui.calibration.progress import ProgressWidgetHandler
from ops.calibration.event import CalibrationStarted, CalibrationOver

import gui.mediator
import ops.system


class ProgressWidgetHandlerTests(unittest.TestCase):
    """
    Tests for the :class:`gui.calibration.progress.ProgressWidgetHandler`
    class.
    """

    def setUp(self):
        self.mediator = gui.mediator.Mediator(logging=True)
        self.system = ops.system.ProductionSystem(self.mediator)
        self.handler = ProgressWidgetHandler(self.system)


    def startCalibration(self):
        """Sends a synthetic :class:`CalibrationStarted` event."""
        self.mediator.noteEvent(CalibrationStarted(self.system, 'dummy'))


    def endCalibration(self):
        """Sends a synthetic :class:`CalibrationOver` event."""
        self.mediator.noteEvent(
            CalibrationOver(self.system, 'dummy', 'dummy', 'dummy', 'dummy'))


    def testGC(self):
        """Make sure the class is properly garbage-collected."""
        wr = weakref.ref(self.handler)
        self.handler = None
        gc.collect()
        self.assertEqual(wr(), None)


    def testWidget(self):
        """Tests the :attr:`widget` property."""
        self.assertTrue(isinstance(self.handler.widget, gtk.Widget))
        self.assertRaises(AttributeError, setattr, self.handler, 'widget', 0)


    def testTimeout(self):
        """Checks that a timeout is added when the calibration is started."""
        self.handler.updateInterval = 60000
        self.startCalibration()
        self.assertEqual(self.mediator.timeoutsAdded[-1][0], 60000)


    def testUpdateCalibrationOver(self):
        """
        Tests the :meth:`_update` method when the calibration is over.
        """
        self.startCalibration()
        self.endCalibration()
        self.assertFalse(self.handler._update())


    # FIXME: Needs more tests.



