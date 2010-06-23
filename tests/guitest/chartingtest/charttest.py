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

from gui.charting.axis import *
from test import *
from util import ApplicationError

import gui.charting.chart


class ChartTests(unittest.TestCase):
    """
    Tests for the :mod:`gui.charting.chart` module.
    """

    def setUp(self):
        self.chart = gui.charting.chart.Chart()

        # The chart needs to be realized for some tests.
        self.window = gtk.Window()
        self.chart.size_allocate((0, 0, 1000, 500))
        self.window.add(self.chart)
        self.chart.realize()


    def testAxisProperties(self):
        """Tests that three axis properties."""
        self.assertTrue(isinstance(self.chart.abscissa, Abscissa))
        self.assertTrue(isinstance(self.chart.ordinate, Ordinate))
        self.assertTrue(
            isinstance(self.chart.secondaryOrdinate, SecondaryOrdinate))

        self.assertRaises(TypeError, setattr, self.chart, 'abscissa', None)
        self.assertRaises(TypeError, setattr, self.chart, 'ordinate', None)
        self.assertRaises(
            TypeError, setattr, self.chart, 'secondaryOrdinate', None)


    def testAddFunction(self):
        """Tests the :meth:`addFunction` method."""
        self.assertEqual(len(self.chart.graphs), 0)
        self._addFunctions(self.chart.addFunction)
        self.assertEqual(len(self.chart.graphs), 2)


    def testAddSecondaryFunction(self):
        """Tests the :meth:`addSecondaryFunction` method."""
        self.chart.setSecondaryOrdinate(10000, 'a / b')
        self.assertEqual(len(self.chart.graphs), 0)
        self._addFunctions(self.chart.addSecondaryFunction)
        self.assertEqual(len(self.chart.graphs), 2)


    def _addFunctions(self, method):
        """Utility method that adds two functions to the chart."""
        method(lambda x: x / 2, 'pale goldenrod')
        method(lambda x: x**2, 'lavender blush')


    def testAddPoints(self):
        """Tests the :meth:`addPoints` method."""
        self.assertEqual(len(self.chart.graphs), 0)
        self._addPoints(self.chart.addPoints)
        self.assertEqual(len(self.chart.graphs), 2)


    def testAddSecondaryPoints(self):
        """Tests the :meth:`addSecondaryPoints` method."""
        self.chart.setSecondaryOrdinate(10000, 'a / b')
        self.assertEqual(len(self.chart.graphs), 0)
        self._addPoints(self.chart.addSecondaryPoints)
        self.assertEqual(len(self.chart.graphs), 2)


    def _addPoints(self, method):
        """Utility function that adds two sets of points to the chart."""
        method(((x, x / 2) for x in xrange(100)), 'powder blue')
        method(((x, x**2) for x in xrange(100)), 'bisque')


    def testAddSecondaryError(self):
        """
        Tests the :meth:`addSecondary*` methods without a secondary ordinate.
        """
        self.assertRaises(ApplicationError,
            self._addFunctions, self.chart.addSecondaryFunction)
        self.assertRaises(ApplicationError,
            self._addPoints, self.chart.addSecondaryPoints)


    def testClearGraphs(self):
        """Tests the :meth:`clearGraphs` method."""
        self.chart.setSecondaryOrdinate(100, 'a / b')
        self._addFunctions(self.chart.addFunction)
        self._addFunctions(self.chart.addSecondaryFunction)
        self._addPoints(self.chart.addPoints)
        self._addPoints(self.chart.addSecondaryPoints)
        self.assertNotEqual(len(self.chart.graphs), 0)
        self.chart.clearGraphs()
        self.assertEqual(len(self.chart.graphs), 0)


    def testCaptionText(self):
        """Tests the :attr:`captionText` property."""
        self.chart.captionText = 'This is a caption.'
        self.assertEqual(self.chart.captionText, 'This is a caption.')
        self.chart.captionText = ''
        self.assertEqual(self.chart.captionText, '')
        self.chart.captionText = None
        self.assertEqual(self.chart.captionText, None)


    def testminCaptionLines(self):
        """Tests the :attr:`minCaptionLines` property."""
        self.chart.minCaptionLines = 3
        self.assertEqual(self.chart.minCaptionLines, 3)
        self.chart.minCaptionLines = 0
        self.assertEqual(self.chart.minCaptionLines, 0)
        self.assertRaises(
            ApplicationError, setattr, self.chart, 'minCaptionLines', -1)


    def testExposeHandler(self):
        """Tests the :meth:`_exposeHandler` method."""
        logger = wrapLogger(self.chart._draw)
        self.chart._exposeHandler()
        self.assertEqual(logger.log, [()])


    def testDrawEmpty(self):
        """Tests the :meth:`_draw` method without graphs."""
        self.chart.setAbscissa(100, 'a')
        self.chart._draw()
        self.chart.setSecondaryOrdinate(1, 'a / b')
        # Just check for errors.
        self.chart._draw()
        # And again, since drawing for the first time is a special case.
        self.chart._draw()


    def testDrawNonempty(self):
        """Tests the :meth:`_draw` method with graphs."""
        self.chart.setSecondaryOrdinate(100, 'a / b')
        self._addFunctions(self.chart.addFunction)
        self._addFunctions(self.chart.addSecondaryFunction)
        self._addPoints(self.chart.addPoints)
        self._addPoints(self.chart.addSecondaryPoints)
        # Just check for errors.
        self.chart._draw()
        # And again, since drawing for the first time is a special case.
        self.chart._draw()


    # _drawBackground is covered by testDrawEmpty and testDrawNonempty


    def testDrawCaption(self):
        """Tests the :meth:`_drawCaption` method."""
        self.chart._drawCaption()
        self.assertEqual(self.chart._captionHeight, 0)

        self.chart.minCaptionLines = 1
        self.chart._drawCaption()
        captionHeightOneLine = self.chart._captionHeight
        self.assertTrue(captionHeightOneLine > 0)

        self.chart.minCaptionLines = 0
        self.chart.captionText = 'x'
        self.chart._drawCaption()
        self.assertEqual(self.chart._captionHeight, captionHeightOneLine)

        self.chart.minCaptionLines = 3
        self.chart._drawCaption()
        captionHeightThreeLines = self.chart._captionHeight
        self.assertTrue(captionHeightThreeLines > captionHeightOneLine)

        self.chart.minCaptionLines = 0
        self.chart.captionText = 'x\nx\nx'
        self.chart._drawCaption()
        self.assertEqual(self.chart._captionHeight, captionHeightThreeLines)


    # _drawFrame is covered by testDrawEmpty and testDrawNonempty
    # _drawNoDataMessage is covered by testDrawEmpty


    def testGetChartArea(self):
        """Tests the :meth:`getChartArea` method."""
        oldBorderWidth = gui.charting.chart.BORDER_WIDTH
        try:
            gui.charting.chart.BORDER_WIDTH = (10, 10, 10, 10)
            self.assertEqual(self.chart.getChartArea(), (10, 10, 980, 480))
            gui.charting.chart.BORDER_WIDTH = (100, 100, 100, 100)
            self.assertEqual(self.chart.getChartArea(), (100, 100, 800, 300))
            self.chart._captionHeight = 50
            self.assertEqual(self.chart.getChartArea(), (100, 100, 800, 250))
        finally:
            gui.charting.chart.BORDER_WIDTH = oldBorderWidth


