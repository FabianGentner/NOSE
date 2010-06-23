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

from gui.calibration.entry import TemperatureEntryHandler
from ops.calibration.event import TemperatureRequested, TemperatureRequestOver

import gui.mediator
import ops.system


class TemperatureEntryHandlerTests(unittest.TestCase):
    """
    Tests the :class:`~gui.calibration.entry.TemperatureEntryHandler` class.
    """

    def setUp(self):
        self.temperature = None

        self.mediator = gui.mediator.Mediator()
        self.system = ops.system.ProductionSystem(self.mediator)
        self.handler = TemperatureEntryHandler(self.system)

        # The widget needs to be in a window for some of the tests.
        self.window = gtk.Window()
        self.windowBox = gtk.HBox()
        self.windowBox.pack_start(self.handler.box)
        self.windowBox.pack_start(self.handler.button)
        self.window.add(self.windowBox)


    def _callback(self, temperature):
        """The callback sent along with synthetic temperature requests."""
        self.temperature = temperature


    def testGC(self):
        """Make sure the class is properly garbage-collected."""
        wr = weakref.ref(self.handler)
        self.handler = None
        gc.collect()
        self.assertEqual(wr(), None)


    def testWidgets(self):
        """Tests the :attr:`box` and :attr:`button` properties."""
        self.assertTrue(isinstance(self.handler.box, gtk.Widget))
        self.assertRaises(AttributeError, setattr, self.handler, 'box', 0)
        self.assertTrue(isinstance(self.handler.button, gtk.Widget))
        self.assertRaises(AttributeError, setattr, self.handler, 'button', 0)


    def testInitialInsensitivity(self):
        """Test that the widgets are initially insensitive."""
        self.assertFalse(self.handler.box.get_property('sensitive'))
        self.assertFalse(self.handler.button.get_property('sensitive'))


    def testTemperatureRequest(self):
        """Tests the handling of temperature requests."""
        self.mediator.noteEvent(
            TemperatureRequested('dummy', self.system, self._callback))

        self.assertTrue(self.handler._entry.is_focus())
        self.assertTrue(self.handler.box.get_property('sensitive'))
        self.assertFalse(self.handler.button.get_property('sensitive'))


    def testTemperatureRequestOver(self):
        """Tests the handling of canceled temperature requests."""
        self.mediator.noteEvent(
            TemperatureRequested('dummy', self.system, self._callback))
        self.mediator.noteEvent(
            TemperatureRequestOver('dummy', self.system))

        self.assertFalse(self.handler.box.get_property('sensitive'))
        self.assertFalse(self.handler.button.get_property('sensitive'))


    def testOkClicked(self):
        """Tests the :meth:`_okClicked` method."""
        self.mediator.noteEvent(
            TemperatureRequested('dummy', self.system, self._callback))

        self.handler._entry.set_text('0123')
        self.handler._buttonClicked('dummy')
        self.assertEqual(self.temperature, 123)


    def testOkSensitivity(self):
        """Tests that the OK button is only sensitive when its supposed to."""
        self.assertFalse(self.handler.button.get_property('sensitive'))

        tests = (
            ('500',    True),
            ('-100',   False),
            ('0890',   True),
            ('0xA',    False),
            ('1000.1', False),
            ('1000.',  False),
            ('.5',     False))

        for text, result in tests:
            self.handler._entry.set_text(text)
            self.handler._textChanged(self.handler._entry)
            self.assertEquals(
                self.handler.button.get_property('sensitive'), result)


    def testDefault(self):
        """Tests whether the :class:`gtk.Entry` can default."""
        self.assertTrue(self.handler._entry.get_activates_default())
        self.assertTrue(self.handler.button.get_property('has-default'))


    def testPersistentDefault(self):
        """
        Tests whether the :class:`gtk.Entry` regains the default after the
        button has been temporarily removed from its window. (This test
        results in a call to _hierarchyChanged.)
        """
        self.windowBox.remove(self.handler.button)
        self.assertFalse(self.handler.button.get_property('has-default'))
        self.windowBox.add(self.handler.button)
        self.assertTrue(self.handler.button.get_property('has-default'))


