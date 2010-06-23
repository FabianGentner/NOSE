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

"""
This module contains the :class:`FunctionGraph` and :class:`PointGraph`
classes, which are responsible for drawing the graphs shown on a
:class:`~gui.charting.chart.Chart`.

To add these graphs to a :class:`~gui.charting.chart.Chart`, use its
:meth:`~gui.charting.chart.Chart.addGraph` or
:meth:`~gui.charting.chart.Chart.addSecondaryGraph` methods.

A usage example can be found on the documentation page of the
:mod:`gui.charting` package.
"""

from gui.widgets import getColor


###############################################################################
# CONSTANTS                                                                   #
###############################################################################

#: The size of the squares the :class:`PointGraph` uses to mark a point
#: if its style is ``'squares'``, in pixels. Should be odd.
SQUARE_SIZE = 5

#: The size of the diamonds the :class:`PointGraph` uses to mark a point
#: if its style is ``'diamonds'``, in pixels. Should be odd.
DIAMOND_SIZE = int((2 * SQUARE_SIZE ** 2) ** 0.5 // 2 * 2 + 1)


###############################################################################
# FUNCTION GRAPH                                                              #
###############################################################################

class FunctionGraph(object):
    """
    Creates a new graph that draws a continuous line using a function that
    accepts any float value in the displayed range as an input and returns
    a float value.

    Sections of the graph that lie outside the range shown on the graph
    are not drawn. If `drawOnFrame` is ``False``, values at zero and the
    ordinates's maximum value will not be drawn either.

    `color` may be a :class:`gtk.gdk.Color` object, an X11 color name
    (:samp:`'misty rose'`) or a hexadecimal string (:samp:`'#FFE4E1'`).

    .. note::

        The graph draws one *y* value for each pixel of the chart area's width.
        If the function rapidly changes its *y* values back and forth, that
        change may lie between two *x* values for which *y* values are drawn,
        and may thus not appear on the chart.
    """

    def __init__(self, function, color, drawOnFrame=True):
        self._function = function
        self._color = getColor(color)
        self._drawOnFrame = drawOnFrame
        self._graphicsContext = None


    def draw(self, chart, abscissa, ordinate):
        """
        Draws the graph on its :class:`~gui.charting.chart.Chart`. `abscissa`
        and `ordinate` are the :class:`~gui.charting.axis.Axis` instances
        whose dimensions are used for drawing the graph.
        """
        cax, cay, caw, cah = chart.chartArea

        if self._graphicsContext == None:
            self._graphicsContext = chart.window.new_gc()
            self._graphicsContext.foreground = self._color

        gc = self._graphicsContext

        if self._drawOnFrame:
            gc.set_clip_rectangle((cax + 1, cay, caw - 1, cah + 1))
        else:
            gc.set_clip_rectangle((cax + 1, cay + 1, caw - 1, cah - 1))

        lastYPosition = None

        # The loop should be run for the first value, even if it isn't drawn,
        # so that lastYPosition can be set, but it doesn't need to be run for
        # the last value.
        for xPosition in xrange(cax, cax + caw):
            xValue = abscissa.valueFromX(xPosition)
            yValue = self._function(xValue)
            yPosition = ordinate.yFromValue(yValue)

            if lastYPosition != None:
                chart.window.draw_line(gc,
                    xPosition - 1, lastYPosition,
                    xPosition,     yPosition)

            lastYPosition = yPosition



###############################################################################
# POINT GRAPH                                                                 #
###############################################################################

class PointGraph(object):
    """
    Creates a new graph that draws a series of marks representing discrete
    values. Marks that lie outside the ranges shown on the graph are not
    drawn.

    `color` may be a :class:`gtk.gdk.Color` object, an X11 color name
    (:samp:`'misty rose'`) or a hexadecimal string (:samp:`'#FFE4E1'`).

    `style` determines the type of mark used. ``'squares'`` and ``'diamonds'``
    are supported.
    """

    def __init__(self, points, color, style='squares'):
        self._points = tuple(points)
        self._color = getColor(color)
        self._style = style
        self._graphicsContext = None


    def draw(self, chart, abscissa, ordinate):
        """
        Draws the graph on its :class:`~gui.charting.chart.Chart`. `abscissa`
        and `ordinate` are the :class:`~gui.charting.axis.Axis` instances
        whose dimensions are used for drawing the graph.
        """
        if self._graphicsContext == None:
            self._graphicsContext = chart.window.new_gc()
            self._graphicsContext.foreground = self._color

        gc = self._graphicsContext

        for xValue, yValue in self._points:
            onAbscissa = abscissa.isInBounds(xValue)
            onOrdinate = ordinate.isInBounds(yValue)

            if onAbscissa and onOrdinate:
                xPosition = chart.abscissa.xFromValue(xValue)
                yPosition = ordinate.yFromValue(yValue)

                if self._style == 'squares':
                    chart.window.draw_rectangle(gc, True,
                        xPosition - SQUARE_SIZE // 2,
                        yPosition - SQUARE_SIZE // 2,
                        SQUARE_SIZE, SQUARE_SIZE)

                if self._style == 'diamonds':
                    # ISSUE: The various +1 and -1 are necessary to correctly
                    # draw the diamonds. I've discovered that fact by trial
                    # and error rather than by understanding the underlying
                    # issue, though. The points work for DIAMOND_SIZEs up to
                    # at least 15, however.
                    chart.window.draw_polygon(gc, True,
                        ((xPosition, yPosition - DIAMOND_SIZE // 2 - 1),
                         (xPosition + DIAMOND_SIZE // 2 + 1, yPosition),
                         (xPosition, yPosition + DIAMOND_SIZE // 2 + 1),
                         (xPosition - DIAMOND_SIZE // 2, yPosition)))

