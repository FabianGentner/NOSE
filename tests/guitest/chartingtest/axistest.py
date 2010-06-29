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

import gtk
import unittest

from test import *
from gui.charting.axis import *

import gui.charting.chart


class AxisTests(unittest.TestCase):
    """
    Tests for functionality common to all :class:`gui.charting.axis.Axis`
    subclasses.
    """

    def setUp(self):
        self.chart = gui.charting.chart.Chart()
        self.abscissa = self.chart.abscissa
        self.ordinate = self.chart.ordinate
        self.ordinate2 = self.chart.secondaryOrdinate

        self.axes = (self.abscissa, self.ordinate, self.ordinate2)

        self.oldMinTickDistance = gui.charting.axis.MIN_TICK_DISTANCE
        self.oldAbscissaMinTickLabelDistance = \
            gui.charting.axis.ABSCISSA_MIN_TICK_LABEL_DISTANCE
        self.oldOrdinateMinTickLabelDistance = \
            gui.charting.axis.ORDINATE_MIN_TICK_LABEL_DISTANCE

        # The chart needs to be realized for some tests.
        window = gtk.Window()
        self.chart.size_allocate((0, 0, 300, 300))
        window.add(self.chart)
        self.chart.realize()


    def tearDown(self):
        gui.charting.axis.MIN_TICK_DISTANCE = self.oldMinTickDistance
        gui.charting.axis.ABSCISSA_MIN_TICK_LABEL_DISTANCE = \
            self.oldAbscissaMinTickLabelDistance
        gui.charting.axis.ORDINATE_MIN_TICK_LABEL_DISTANCE = \
            self.oldOrdinateMinTickLabelDistance


    def testClasses(self):
        """Checks that the correct classes are used for the axes."""
        self.assertTrue(isinstance(self.abscissa, Abscissa))
        self.assertTrue(isinstance(self.ordinate, Ordinate))
        self.assertTrue(isinstance(self.ordinate2, SecondaryOrdinate))


    def testCreateAxis(self):
        """Tries creating an :class:`Axis`."""
        self.assertRaises(TypeError, gui.charting.axis.Axis, None)


    def testMaxValue(self):
        """Tests the :attr:`maxValue` property."""
        logger = replaceWithLogger(self.chart.queue_draw)

        for a, test in enumerate((100.0, 75, 0.5, 10.0)):
            for b, axis in enumerate(self.axes, start=1):
                axis.maxValue = test
                self.assertEqual(axis.maxValue, test)
                self.assertTrue(isinstance(axis.maxValue, float))
                self.assertEqual(len(logger.log), 3 * a + b)

        for test in (0.0, 0.00001, -10, -23.0):
            for axis in self.axes:
                self.assertRaises(ValueError, setattr, axis, 'maxValue', test)


    def testdimensionLabelText(self):
        """Test the :attr:`dimensionLabelText` property."""
        logger = replaceWithLogger(self.chart.queue_draw)

        for a, text in enumerate(('a', 'a / b', 'a / b / c', '', None)):
            for b, axis in enumerate(self.axes, start=1):
                axis.dimensionLabelText = text
                self.assertEqual(axis.dimensionLabelText, text)
                self.assertEqual(len(logger.log), 3 * a + b)


    def testDraw(self):
        """Tests the :meth:`draw` method."""
        for axis in self.axes:
            axis.draw()   # Just make sure there are no errors.


    # _drawTick and _drawTickLabel are covered by testDraw.


    def testDrawDimensionLabel(self):
        """Tests the :meth:`_drawDimensionLabel` method."""
        for axis in self.axes:
            axis.draw()   # Required to set the graphics context.
            for text in ('a', 'a / b', 'a / b / c'):
                axis.dimensionLabelText = text
                axis._drawDimensionLabel()


    # _drawSimpleDimensionLabel and _drawDimensionLabelFraction are covered
    # by testDrawDimensionLabel.


    def testIsInBounds(self):
        """Tests the :meth:`isInBounds` method."""
        for axis in self.axes:
            axis.maxValue = 100
            self.assertTrue(axis.isInBounds(0))
            self.assertTrue(axis.isInBounds(25))
            self.assertTrue(axis.isInBounds(100))
            self.assertFalse(axis.isInBounds(-10))
            self.assertFalse(axis.isInBounds(120))

            axis.maxValue = 1.5
            self.assertTrue(axis.isInBounds(0.0))
            self.assertTrue(axis.isInBounds(0.25))
            self.assertTrue(axis.isInBounds(1.5))
            self.assertFalse(axis.isInBounds(-1.0))
            self.assertFalse(axis.isInBounds(2.3))


    def testTickValues(self):
        """Tests the :meth:`_tickValues` method."""
        # Constants are reset in tearDown.
        gui.charting.axis.ABSCISSA_MIN_TICK_LABEL_DISTANCE = 50
        gui.charting.axis.ORDINATE_MIN_TICK_LABEL_DISTANCE = 50

        minor = gui.charting.axis.MINOR_TICK_LENGTH
        major = gui.charting.axis.MAJOR_TICK_LENGTH

        for axis in self.axes:
            # Major labels only; major max; not all space used:
            gui.charting.axis.MIN_TICK_DISTANCE = 15
            axis._getLength = lambda: 250
            axis.maxValue = 30
            self.assertEqual(tuple(axis._tickValues()),
                ((0, major, '0'), (10, major, '10'), (20, major, '20'),
                (30, major, '30')))

            # Major labels and half labels; minor max; all space used:
            gui.charting.axis.MIN_TICK_DISTANCE = 15
            axis._getLength = lambda: 250
            axis.maxValue = 25
            self.assertEqual(tuple(axis._tickValues()),
                ((0, major, '0'), (5, minor, '5'), (10, major, '10'),
                (15, minor, '15'), (20, major, '20'), (25, minor, '25')))

            # Fifth labels only; unlabeled max; not all space used:
            gui.charting.axis.MIN_TICK_DISTANCE = 40
            axis._getLength = lambda: 250
            axis.maxValue = 9
            self.assertEqual(tuple(axis._tickValues()),
                ((0, major, '0'), (2, minor, '2'), (4, minor, '4'),
                (6, minor, '6'), (8, minor, '8')))

            # Major labels and tenth ticks; unticked max; not all space used.
            # Also serves as a regression test for a bug that would sometimes
            # cause Axes with a maxValue that is not a multiple of a power of
            # ten to chose a stride that is an order of magnitude higher than
            # necessary, or to inadvertently omit tenth ticks or minor labels,
            # because the space above the last tick wasn't taken into account.
            gui.charting.axis.MIN_TICK_DISTANCE = 5
            axis._getLength = lambda: 60
            axis.maxValue = 10.5
            self.assertEqual(tuple(axis._tickValues()),
                ((0, major, '0'), (1, minor, None), (2, minor, None),
                (3, minor, None), (4, minor, None), (5, minor, None),
                (6, minor, None), (7, minor, None), (8, minor, None),
                (9, minor, None), (10, major, '10')))

            # Major labels, half labels, and tenth ticks; not all space used.
            # Also serves as a regression test for a bug that would sometimes
            # cause tenth ticks or minor labels for the maxValue of an Axis to
            # be omitted because of an issue with floating-point precision.
            gui.charting.axis.MIN_TICK_DISTANCE = 10
            axis._getLength = lambda: 250
            axis.maxValue = 110
            self.assertEqual(tuple(axis._tickValues()),
                ((0, major, '0'),  (10, minor, None), (20, minor, None),
                (30, minor, None), (40, minor, None), (50, minor, '50'),
                (60, minor, None), (70, minor, None), (80, minor, None),
                (90, minor, None), (100, major, '100'), (110, minor, None)))

            # Major labels, fifth labels, and tenth ticks; all space used:
            gui.charting.axis.MIN_TICK_DISTANCE = 15
            axis._getLength = lambda: 250
            axis.maxValue = 100
            self.assertEqual(tuple(axis._tickValues()),
                ((0, major, '0'),  (10, minor, None), (20, minor, '20'),
                (30, minor, None), (40, minor, '40'), (50, minor, None),
                (60, minor, '60'), (70, minor, None), (80, minor, '80'),
                (90, minor, None), (100, major, '100')))


            ### SPECIAL CASE ##################################################

            # No half labels because of the special case for stide == 1 and
            # max >= 2.0:
            gui.charting.axis.MIN_TICK_DISTANCE = 15
            axis._getLength = lambda: 250
            axis.maxValue = 2.5
            self.assertEqual(tuple(axis._tickValues()),
                ((0, major, '0'), (1.0, major, '1'), (2.0, major, '2')))

            # Special case does not apply since max < 2.0:
            gui.charting.axis.MIN_TICK_DISTANCE = 30
            axis._getLength = lambda: 250
            axis.maxValue = 1.4
            self.assertEqual(tuple(axis._tickValues()),
                ((0, major, '0'), (0.5, minor, '0.5'), (1.0, major, '1')))


            ### FALLBACK ######################################################

            # Not enough space for any labels; use fallback:
            gui.charting.axis.MIN_TICK_DISTANCE = 1
            axis._getLength = lambda: 40
            axis.maxValue = 0.9
            self.assertEqual(tuple(axis._tickValues()),
                ((0, major, '0'), (0.9, major, '0.9')))


    # _getInkExtends are covered by testDrawDimensionLabel.


###############################################################################
# TESTS FOR ABSCISSA                                                          #
###############################################################################

class AbscissaTests(unittest.TestCase):
    """
    Tests for the :class:`Abscissa` class.
    """

    def setUp(self):
        self.chart = gui.charting.chart.Chart()
        self.chart._chartArea = (50, 50, 200, 100)
        self.abscissa = self.chart.abscissa

        self.oldLabelSpacing =  gui.charting.axis.ABSCISSA_TO_LABEL_SPACING
        self.oldDimensionLabelPosition = \
            gui.charting.axis.ABSCISSA_DIMENSION_LABEL_POSITION

        gui.charting.axis.ABSCISSA_TO_LABEL_SPACING = 10
        gui.charting.axis.ABSCISSA_DIMENSION_LABEL_POSITION = (10, 20)


    def tearDown(self):
        gui.charting.axis.ABSCISSA_TO_LABEL_SPACING = self.oldLabelSpacing
        gui.charting.axis.ABSCISSA_DIMENSION_LABEL_POSITION = \
            self.oldDimensionLabelPosition


    def testXFromValue(self):
        """Tests the :meth:`xFromValue` method."""
        self.abscissa.maxValue = 100
        self.assertEqual(self.abscissa.xFromValue(0), 50)
        self.assertEqual(self.abscissa.xFromValue(25), 100)
        self.assertEqual(self.abscissa.xFromValue(100), 250)


    def testValueFromX(self):
        """Tests the valueFromX method of Abscissa."""
        self.abscissa.maxValue = 100
        self.assertEqual(self.abscissa.valueFromX(50), 0.0)
        self.assertEqual(self.abscissa.valueFromX(100), 25.0)
        self.assertEqual(self.abscissa.valueFromX(250), 100.0)


    def testGetMinTickLabelDistance(self):
        """Tests the :meth:`_getMinTickLabelDistance` method."""
        self.assertEqual(self.abscissa._getMinTickLabelDistance(),
            gui.charting.axis.ABSCISSA_MIN_TICK_LABEL_DISTANCE)


    # _drawTick is covered by testDraw in AxisTests.


    def testGetTickLabelPosition(self):
        """Tests the :meth:`_getTickLabelPosition` method."""
        self.abscissa.maxValue = 100
        self.assertEqual(
            self.abscissa._getTickLabelPosition(50, 11, 15), (145, 160))


    def testGetDimensionLabelPosition(self):
        """Tests the :meth:`_getDimensionLabelPosition` method."""
        self.abscissa.maxValue = 100
        self.assertEqual(
            self.abscissa._getDimensionLabelPosition(11, 35), (260, 170))


    def testGetY(self):
        """Tests the :meth:`_getY` method."""
        self.assertEqual(self.abscissa._getY(), 150)


    def testGetEndX(self):
        """Tests the :meth:`_getEndX` method."""
        self.assertEqual(self.abscissa._getEndX(), 250)


    def testGetLength(self):
        """Tests the :meth:`_getLength` method."""
        self.assertEqual(self.abscissa._getLength(), 200)


###############################################################################
# TESTS FOR ORDINATE                                                          #
###############################################################################

class OrdinateTests(unittest.TestCase):
    """
    Tests for the :class:`Ordinate` and :class:`SecondaryOrdinate` classes.
    """

    def setUp(self):
        self.chart = gui.charting.chart.Chart()
        self.chart._chartArea = (50, 50, 200, 100)
        self.ordinate = self.chart.ordinate
        self.ordinate2 = self.chart.secondaryOrdinate

        self.oldLabelSpacing =  gui.charting.axis.ORDINATE_TO_LABEL_SPACING
        self.oldDimensionLabelPosition = \
            gui.charting.axis.ORDINATE_DIMENSION_LABEL_POSITION

        gui.charting.axis.ORDINATE_TO_LABEL_SPACING = 10
        gui.charting.axis.ORDINATE_DIMENSION_LABEL_POSITION = (20, 10)


    def tearDown(self):
        gui.charting.axis.ORDINATE_TO_LABEL_SPACING = self.oldLabelSpacing
        gui.charting.axis.ORDINATE_DIMENSION_LABEL_POSITION = \
            self.oldDimensionLabelPosition


    def testYFromValue(self):
        """Tests the :meth:`yFromValue` method."""
        for axis in (self.ordinate, self.ordinate2):
            axis.maxValue = 100
            self.assertEqual(axis.yFromValue(0), 150)
            self.assertEqual(axis.yFromValue(25), 125)
            self.assertEqual(axis.yFromValue(100), 50)


    def testYFromValueOutsideRange(self):
        """Tests :meth:`yFromValue` with values outside the range."""
        for axis in (self.ordinate, self.ordinate2):
            axis.maxValue = 100
            self.assertEqual(axis.yFromValue(-25), 175)
            self.assertEqual(axis.yFromValue(200), -50)


    def testValueFromY(self):
        """Tests the :meth:`valueFromY` method."""
        for axis in (self.ordinate, self.ordinate2):
            axis = self.ordinate
            axis.maxValue = 100
            self.assertEqual(axis.valueFromY(150), 0.0)
            self.assertEqual(axis.valueFromY(125), 25.0)
            self.assertEqual(axis.valueFromY(50), 100.0)


    def testGetMinTickLabelDistance(self):
        """Tests the :meth:`_getMinTickLabelDistance` method."""
        self.assertEqual(self.ordinate._getMinTickLabelDistance(),
            gui.charting.axis.ORDINATE_MIN_TICK_LABEL_DISTANCE)
        self.assertEqual(self.ordinate2._getMinTickLabelDistance(),
            gui.charting.axis.ORDINATE_MIN_TICK_LABEL_DISTANCE)


    # _drawTick is covered by testDraw in AxisTests.


    def testGetTickLabelPosition(self):
        """Tests the :meth:`_getTickLabelPosition` method."""
        for axis, x in ((self.ordinate, 29), (self.ordinate2, 260)):
            axis.maxValue = 100
            axis.tickLabelDistance = 10
            self.assertEqual(axis._getTickLabelPosition(50, 11, 15), (x, 93))


    def testGetDimensionLabelPosition(self):
        """Tests the :meth:`_getDimensionLabelPosition` method."""
        for axis, x in ((self.ordinate, 19), (self.ordinate2, 270)):
            axis.maxValue = 100
            axis.dimensionLabelDistance = (20, 10)
            self.assertEqual(axis._getDimensionLabelPosition(11, 35), (x, 5))


    def testGetX(self):
        """Tests the :meth:`_getX` method."""
        self.assertEqual(self.ordinate._getX(), 50)
        self.assertEqual(self.ordinate2._getX(), 250)


    def testGetEndY(self):
        """Tests the :meth:`_getEndY` method."""
        for axis in (self.ordinate, self.ordinate2):
            self.assertEqual(axis._getEndY(), 50)


    def testGetLength(self):
        """Tests the :meth:`_getLength` method."""
        self.assertEqual(self.ordinate._getLength(), 100)
        self.assertEqual(self.ordinate2._getLength(), 100)

