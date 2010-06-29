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

        self.assertRaises(
            AttributeError, setattr, self.chart, 'abscissa', None)
        self.assertRaises(
            AttributeError, setattr, self.chart, 'ordinate', None)
        self.assertRaises(
            AttributeError, setattr, self.chart, 'secondaryOrdinate', None)


    def testShowSecondaryOrdinate(self):
        """Tests the :attr:`showSecondaryOrdinate` property."""
        logger = replaceWithLogger(self.chart.queue_draw)
        self.assertFalse(self.chart.showSecondaryOrdinate)
        self.chart.showSecondaryOrdinate = True
        self.assertTrue(self.chart.showSecondaryOrdinate)
        self.assertEqual(len(logger.log), 1)


    def testGraphs(self):
        """
        Tests the :meth:`addGraph`, :meth:`addSecondaryGraph` and
        :meth:`clearGraphs` methods.
        """
        s = Stub(None, draw=fun(None))
        o1 = self.chart.ordinate
        o2 = self.chart.secondaryOrdinate

        logger = replaceWithLogger(self.chart.queue_draw)

        self.assertEqual(self.chart._graphs, [])
        self.chart.addGraph(s)
        self.assertEqual(self.chart._graphs, [(s, o1)])
        self.assertEqual(len(logger.log), 1)
        self.chart.addGraph(s)
        self.assertEqual(self.chart._graphs, [(s, o1), (s, o1)])
        self.assertEqual(len(logger.log), 2)
        self.chart.addSecondaryGraph(s)
        self.assertEqual(self.chart._graphs, [(s, o1), (s, o1), (s, o2)])
        self.assertEqual(len(logger.log), 3)
        self.chart.clearGraphs()
        self.assertEqual(self.chart._graphs, [])
        self.assertEqual(len(logger.log), 4)
        self.chart.addSecondaryGraph(s)
        self.assertEqual(self.chart._graphs, [(s, o2)])
        self.assertEqual(len(logger.log), 5)
        self.chart.addGraph(s)
        self.assertEqual(self.chart._graphs, [(s, o2), (s, o1)])
        self.assertEqual(len(logger.log), 6)


    def testCaptionText(self):
        """Tests the :attr:`captionText` property."""
        queueDrawLogger = replaceWithLogger(self.chart.queue_draw)
        updateChartAreaLogger = replaceWithLogger(self.chart._updateChartArea)

        self.chart.captionText = 'This is a caption.'
        self.assertEqual(self.chart.captionText, 'This is a caption.')
        self.assertEqual(len(queueDrawLogger.log), 1)
        self.assertEqual(len(updateChartAreaLogger.log), 1)

        self.chart.captionText = ''
        self.assertEqual(self.chart.captionText, '')
        self.assertEqual(len(queueDrawLogger.log), 2)
        self.assertEqual(len(updateChartAreaLogger.log), 2)

        self.chart.captionText = None
        self.assertEqual(self.chart.captionText, None)
        self.assertEqual(len(queueDrawLogger.log), 3)
        self.assertEqual(len(updateChartAreaLogger.log), 3)


    def testMinCaptionLines(self):
        """Tests the :attr:`minCaptionLines` property."""
        queueDrawLogger = replaceWithLogger(self.chart.queue_draw)
        updateChartAreaLogger = replaceWithLogger(self.chart._updateChartArea)

        self.chart.minCaptionLines = 3
        self.assertEqual(self.chart.minCaptionLines, 3)
        self.assertEqual(len(queueDrawLogger.log), 1)
        self.assertEqual(len(updateChartAreaLogger.log), 1)

        self.chart.minCaptionLines = 0
        self.assertEqual(self.chart.minCaptionLines, 0)
        self.assertEqual(len(queueDrawLogger.log), 2)
        self.assertEqual(len(updateChartAreaLogger.log), 2)

        self.assertRaises(
            ValueError, setattr, self.chart, 'minCaptionLines', -1)
        self.assertEqual(len(queueDrawLogger.log), 2)
        self.assertEqual(len(updateChartAreaLogger.log), 2)


    def testChartArea(self):
        """Tests the :attr:`chartArea` property."""
        self.chart._chartArea = 'dummy'
        self.assertEqual(self.chart.chartArea, 'dummy')

        self.assertRaises(AttributeError, setattr, self.chart, 'chartArea',
            gui.charting.chart.Border(10, 10, 10, 10))


    def testUpdateChartArea(self):
        """Tests the :meth:`_updateChartArea` method."""
        oldBorder = gui.charting.chart.BORDER
        Border = gui.charting.chart.Border
        try:
            gui.charting.chart.BORDER = Border(10, 10, 10, 10)
            self.chart._updateChartArea()
            self.assertEqual(self.chart.chartArea, (10, 10, 980, 480))

            gui.charting.chart.BORDER = Border(100, 100, 100, 100)
            self.chart._updateChartArea()
            self.assertEqual(self.chart.chartArea, (100, 100, 800, 300))

            def fakeGetPixelSize():
                return (
                    1000,
                    self.chart._captionLayout.get_text().count('\n') * 25 + 25)

            self.chart._captionLayout.get_pixel_size = fakeGetPixelSize

            self.chart.minCaptionLines = 2
            self.chart._updateChartArea()
            self.assertEqual(self.chart.chartArea, (100, 100, 800, 250))

            self.chart.captionText = 'foo'
            self.chart._updateChartArea()
            self.assertEqual(self.chart.chartArea, (100, 100, 800, 250))

            self.chart.minCaptionLines = 0
            self.chart._updateChartArea()
            self.assertEqual(self.chart.chartArea, (100, 100, 800, 275))

            self.chart.captionText = 'foo\nbar\nbaz\nqux\nquux'
            self.chart._updateChartArea()
            self.assertEqual(self.chart.chartArea, (100, 100, 800, 175))

            self.chart.minCaptionLines = 2
            self.chart._updateChartArea()
            self.assertEqual(self.chart.chartArea, (100, 100, 800, 175))

            self.chart.minCaptionLines = 6
            self.chart._updateChartArea()
            self.assertEqual(self.chart.chartArea, (100, 100, 800, 150))
        finally:
            gui.charting.chart.BORDER = oldBorder


    def testDraw(self):
        """Tests the :meth:`_draw` method."""
        createGCsLogger = wrapLogger(self.chart._createGraphicsContexts)
        drawBackgroundLogger = wrapLogger(self.chart._drawBackground)
        drawRectangleLogger = wrapLogger(self.chart._drawChartAreaRectangle)
        drawCaptionLogger = wrapLogger(self.chart._drawCaption)
        drawAxesLogger = wrapLogger(self.chart._drawAxes)
        drawGraphsLogger = wrapLogger(self.chart._drawGraphs)
        drawNoDataMessageLogger = wrapLogger(self.chart._drawNoDataMessage)

        self.chart._draw()
        self.assertEqual(len(createGCsLogger.log), 1)
        self.assertEqual(len(drawGraphsLogger.log), 0)
        self.assertEqual(len(drawNoDataMessageLogger.log), 1)

        self.chart._draw()
        self.assertEqual(len(createGCsLogger.log), 1)
        self.assertEqual(len(drawGraphsLogger.log), 0)
        self.assertEqual(len(drawNoDataMessageLogger.log), 2)

        self.chart.addGraph(Stub(None, draw=fun(None)))
        self.chart._draw()
        self.assertEqual(len(createGCsLogger.log), 1)
        self.assertEqual(len(drawGraphsLogger.log), 1)
        self.assertEqual(len(drawNoDataMessageLogger.log), 2)

        self.assertEqual(len(drawBackgroundLogger.log), 3)
        self.assertEqual(len(drawRectangleLogger.log), 3)
        self.assertEqual(len(drawCaptionLogger.log), 3)
        self.assertEqual(len(drawAxesLogger.log), 3)


    # _createGraphicsContexts is covered by testDraw
    # _drawBackground is covered by testDraw
    # _drawChartAreaRectangle is covered by testDraw


    def testDrawCaption(self):
        """Tests the :meth:`_drawCaption` method."""
        logger = replaceWithLogger(self.chart.window.draw_layout)

        self.chart.captionText = 'foo'
        self.chart._drawCaption()
        self.assertEqual(len(logger.log), 0)

        self.chart.addGraph(Stub(None, draw=fun(None)))
        self.chart._drawCaption()
        self.assertEqual(len(logger.log), 1)

        self.chart.captionText = ''
        self.chart._drawCaption()
        self.assertEqual(len(logger.log), 1)

        self.chart.captionText = None
        self.chart._drawCaption()
        self.assertEqual(len(logger.log), 1)


    def testDrawAxes(self):
        """Tests the :meth:`_drawAxes` method."""
        aLogger = replaceWithLogger(self.chart.abscissa.draw)
        oLogger = replaceWithLogger(self.chart.ordinate.draw)
        o2Logger = replaceWithLogger(self.chart.secondaryOrdinate.draw)

        self.chart._drawAxes()
        self.assertEqual(len(aLogger.log), 1)
        self.assertEqual(len(oLogger.log), 1)
        self.assertEqual(len(o2Logger.log), 0)

        self.chart.showSecondaryOrdinate = True
        self.chart._drawAxes()
        self.assertEqual(len(aLogger.log), 2)
        self.assertEqual(len(oLogger.log), 2)
        self.assertEqual(len(o2Logger.log), 1)

        self.chart.showSecondaryOrdinate = False
        self.chart._drawAxes()
        self.assertEqual(len(aLogger.log), 3)
        self.assertEqual(len(oLogger.log), 3)
        self.assertEqual(len(o2Logger.log), 1)


    def testDrawGraphs(self):
        """Tests the :meth:`_drawGraphs` method."""
        stub1 = Stub(None, draw=fun(None))
        stub2 = Stub(None, draw=fun(None))

        self.chart.addGraph(stub1)
        self.chart.addSecondaryGraph(stub2)

        self.chart._drawGraphs()

        self.assertEqual(stub1.log,
            [('draw',
              (self.chart, self.chart.abscissa, self.chart.ordinate),
              None)])
        self.assertEqual(stub2.log, [])

        self.chart.showSecondaryOrdinate = True
        self.chart._drawGraphs()
        self.assertEqual(len(stub1.log), 2)
        self.assertEqual(stub2.log,
            [('draw',
             (self.chart, self.chart.abscissa, self.chart.secondaryOrdinate),
             None)])


    # _drawNoDataMessage is covered by testDraw

