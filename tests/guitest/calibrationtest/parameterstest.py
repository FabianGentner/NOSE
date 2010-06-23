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

from gui.calibration.parameters import ParameterWidgetHandler

import gui.mediator
import ops.system


class ParameterWidgetHandlerTests(unittest.TestCase):
    """
    Tests for the :class:`~gui.calibration.parameters.ParameterWidgetHandler`
    class.
    """

    def setUp(self):
        gui.calibration.parameters.BEEP = False
        self.mediator = gui.mediator.Mediator()
        self.system = ops.system.ProductionSystem(self.mediator)
        self.system.heatingCurrentInSafeMode = 2.0
        self.system.maxHeatingCurrent = 36.0
        self.handler = ParameterWidgetHandler(self.system)


    def tearDown(self):
        gui.calibration.parameters.BEEP = True


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


    def testDefaultValues(self):
        """Test the default values for starting current and max current."""
        self.assertEqual(self.handler._startingCurrent, 2.0)
        self.assertEqual(self.handler._maxCurrent, 36.0)


    def testGetCurrents(self):
        """Tests the getCurrents method."""
        def test(iStart, iStep, iMax, expected):
            self.handler._startingCurrent = iStart
            self.handler._currentIncrement = iStep
            self.handler._maxCurrent = iMax
            self.assertEqual(self.handler.getCurrents(), expected)

        test(2.0, 4.0, 18.0, (2.0, 6.0, 10.0, 14.0, 18.0))
        test(6.0, 0.5,  8.0, (6.0, 6.5,  7.0,  7.5,  8.0))
        test(4.0, 3.0, 12.0, (4.0, 7.0, 10.0))
        test(8.0, 1.0,  8.0, (8.0,))
        test(7.0, 4.0, 10.0, (7.0,))


    def testStartingCurrentInputs(self):
        """Tests a number of legal and illegal starting currents."""
        realValue = gui.calibration.parameters.MIN_CURRENT
        try:
            gui.calibration.parameters.MIN_CURRENT = 0.5
            self.handler._maxCurrent = 12.0

            tests = (
                ('-1000',   0.5),
                ('0',       0.5),
                ('0.25',    0.5),
                ('0.5',     0.5),
                ('.9',      0.9),
                ('5.0',     5.0),
                ('6.',      6.0),
                ('7',       7.0),
                ('08',      8.0),
                ('12.0',   12.0),
                ('1000',   12.0))

            for test in tests:
                self.assertInputEqual('_startingCurrent', *test)
        finally:
            gui.calibration.parameters.MIN_CURRENT = realValue


    def testCurrentIncrementInputs(self):
        """Tests a number of legal and illegal current increments."""
        realValue = gui.calibration.parameters.MIN_CURRENT_INCREMENT
        try:
            gui.calibration.parameters.MIN_CURRENT_INCREMENT = 0.5

            tests = (
                ('-1000',   0.5),
                ('0',       0.5),
                ('0.25',    0.5),
                ('0.5',     0.5),
                ('.9',      0.9),
                ('5.0',     5.0),
                ('6.',      6.0),
                ('7',       7.0),
                ('08',      8.0),
                ('1000', 1000.0))

            for test in tests:
                self.assertInputEqual('_currentIncrement', *test)
        finally:
            gui.calibration.parameters.MIN_CURRENT_INCREMENT = realValue


    def testMaxCurrentInputs(self):
        """Tests a number of legal and illegal max currents."""
        self.handler._startingCurrent = 6.0

        tests = (
            ('-1000',    6.0),
            ('0',        6.0),
            ('3.0',      6.0),
            ('6.0',      6.0),
            ('10.0',    10.0),
            ('11.',     11.0),
            ('12',      12.0),
            ('013',     13.0),
            ('36.0',    36.0),
            ('1000',    36.0))

        for test in tests:
            self.assertInputEqual('_maxCurrent', *test)


    def testStartingCurrentInputsWithChangedMaxCurrent(self):
        """
        Tests the entry of some legal and illegal starting currents after the
        max current has been lowered.
        """
        self.assertInputEqual('_maxCurrent',      '6.0', 6.0)
        self.assertInputEqual('_startingCurrent', '6.0', 6.0)
        self.assertInputEqual('_startingCurrent', '7.0', 6.0)
        self.assertInputEqual('_maxCurrent',      '7.0', 7.0)
        self.assertInputEqual('_startingCurrent', '7.0', 7.0)
        self.assertInputEqual('_startingCurrent', '8.0', 7.0)


    def testMaxCurrentInputsWithChangedStartingCurrent(self):
        """
        Tests the entry of some legal and illegal max currents after the
        starting current has been increased.
        """
        self.assertInputEqual('_startingCurrent', '12.0', 12.0)
        self.assertInputEqual('_maxCurrent',      '12.0', 12.0)
        self.assertInputEqual('_maxCurrent',      '11.0', 12.0)
        self.assertInputEqual('_startingCurrent', '11.0', 11.0)
        self.assertInputEqual('_maxCurrent',      '11.0', 11.0)
        self.assertInputEqual('_maxCurrent',      '10.0', 11.0)


    def testNonNumericInputs(self):
        """Non-numeric inputs must be ignored."""
        tests = ('Fnord!', '', ' ', '1000,0', '1,000.0', '123 abc', u'\u12345')

        for name in ('_startingCurrent', '_currentIncrement', '_maxCurrent'):
            old = getattr(self.handler, name)
            for test in tests:
                self.assertInputEqual(name, test, old)


    def testInputRounding(self):
        """"Tests the limit of the input's fractional digits."""
        digits = gui.calibration.parameters.MAX_FRACTIONAL_DIGITS
        text = '10.12345678901234567890'
        expected = round(float(text), digits)
        for prefix in ('_startingCurrent', '_currentIncrement', '_maxCurrent'):
            self.assertInputEqual(prefix, text, expected)


    def assertInputEqual(self, name, text, expectedValue):
        """
        An utility method that does the actual testing for the methods above.
        """
        entry = getattr(self.handler, name + 'Entry')
        entry.set_text(text)
        self.handler._handleParameterChange(entry, None, name)
        self.assertEqual(getattr(self.handler, name), expectedValue)
        self.assertEqual(entry.get_text(), str(expectedValue))


    def testReturnKey(self):
        """Tests the use of the return key in the entries."""
        event = EventStub('Return')
        for name in ('_startingCurrent', '_currentIncrement', '_maxCurrent'):
            entry = getattr(self.handler, name + 'Entry')
            entry.set_text('6.0')
            self.assertTrue(
                self.handler._handleSpecialKeyPresses(entry, event, name))
            self.assertEqual(getattr(self.handler, name), 6.0)


    def testEscapeKey(self):
        """Tests the use of the escape key in the entries."""
        event = EventStub('Escape')
        for name in ('_startingCurrent', '_currentIncrement', '_maxCurrent'):
            entry = getattr(self.handler, name + 'Entry')
            oldText = entry.get_text()
            oldValue = getattr(self.handler, name)
            entry.set_text('6.0')
            self.assertTrue(
                self.handler._handleSpecialKeyPresses(entry, event, name))
            self.assertEqual(entry.get_text(), oldText)
            self.assertEqual(getattr(self.handler, name), oldValue)


    def testRandomKey(self):
        """Tests the use of some random, nonspecial key in the entries."""
        event = EventStub('SomeRandomNonspecialKey')
        for name in ('_startingCurrent', '_currentIncrement', '_maxCurrent'):
            entry = getattr(self.handler, name + 'Entry')
            self.assertFalse(
                self.handler._handleSpecialKeyPresses(entry, event, name))


class EventStub(object):
    def __init__(self, keyName):
        self.keyval = gtk.gdk.keyval_from_name(keyName)

