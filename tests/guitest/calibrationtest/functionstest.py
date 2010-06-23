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

from gui.calibration.functions import *
from ops.calibration.data import CalibrationData
from test import *

import gui.mediator
import ops.system


class FunctionWidgetTests(unittest.TestCase):
    """
    Tests for the :mod:`gui.calibration.functions` package.
    """

    def setUp(self):
        self.mediator = gui.mediator.Mediator()
        self.system = ops.system.ProductionSystem(self.mediator)
        self.handler = FunctionWidgetHandler(self.system)
        self.cd = makeCalibrationData()
        self.system.calibrationData = self.cd


    def testCreateFunctionWidgets(self):
        """Tests the :func:`createFunctionWidgets` function."""
        widget = createFunctionWidgets(self.system)
        self.assertNotEqual(widget, None)


    def testWidget(self):
        """Tests the :attr:`widget` property."""
        self.assertEqual(self.handler.widget, self.handler._widget)
        self.assertRaises(AttributeError, setattr, self.handler, 'widget', 0)


    def testEvents(self):
        """Check that the class responds to events."""
        logger = wrapLogger(self.handler._updateWidgets)

        self.system.calibrationData = newCD = CalibrationData()
        self.assertEqual(logger.log, [newCD])

        self.system.calibrationData = self.cd
        self.assertEqual(logger.log, [newCD, self.cd])


    def testFormatPolynomial(self):
        """Tests the :meth:`_formatPolynomial` method."""
        tests = (
            ((1.0, 2.0, 3.0, 4.0),
                '1' + NBSP + 'i' + WJ + '<sup>3</sup> '
                + PLUS + NBSP + '2' + NBSP + 'i' + WJ + '<sup>2</sup> '
                + PLUS + NBSP + '3' + NBSP + 'i '
                + PLUS + NBSP + '4'),
            ((-1.0, -2.0, -3.0, -4.0),
                MINUS + WJ + '1' + NBSP + 'i' + WJ + '<sup>3</sup> '
                + MINUS + NBSP + '2' + NBSP + 'i' + WJ + '<sup>2</sup> '
                + MINUS + NBSP + '3' + NBSP + 'i '
                + MINUS + NBSP + '4'),
            ((0.0, 1.0), '1'),
            ((0.0, -1.0), MINUS + WJ + '1'),
            ((1.0, 0.0), '1' + NBSP + 'i'),
            ((0.0, 1.0, 0.0), '1' + NBSP + 'i'),
            ((1.0, 0.0, 0.0, 4.0),
                '1' + NBSP + 'i' + WJ + '<sup>3</sup> ' + PLUS + NBSP + '4'),
            ((1.0,), '1'),
            ((0.0,), ''),
            ((0.0, 0.0, 0.0), ''),
            ((-0.0, -0.0, -0.0), ''),
            ((), ''))

        for c, x in tests:
            self.assertEqual(self.handler._formatPolynomial(c, 'i'), x)


    def testFormatNumber(self):
        """Tests the :meth:`_formatNumber` method."""
        tests = (
            (1.0, '1'),
            (1234.0, '1234'),
            (12345.0,
                '1.234' + NBSP + TIMES + NBSP + '10' + WJ + '<sup>4</sup>'),
            (10000.0,
                '1' + NBSP + TIMES + NBSP + '10' + WJ + '<sup>4</sup>'),
            (0.0001, '0.0001'),
            (0.00001,
                '1' + NBSP + TIMES + NBSP
                + '10' + WJ + '<sup>' + MINUS + WJ + '5</sup>'),
            (0.000012345,
                '1.234' + NBSP + TIMES + NBSP
                + '10' + WJ + '<sup>' + MINUS + WJ + '5</sup>'),
            (123.45e23,
                '1.234' + NBSP + TIMES + NBSP
                + '10' + WJ + '<sup>' + '25</sup>'),
            (1234.5e-23,
                '1.234' + NBSP + TIMES + NBSP
                + '10' + WJ + '<sup>' + MINUS + WJ + '20</sup>'))

        for n, x in tests:
            self.assertEqual(self.handler._formatNumber(n), x)

