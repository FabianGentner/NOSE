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
This module contains the :class:`Axis` abstract base class and its subclasses
:class:`Abscissa`, :class:`Ordinate`, and :class:`SecondaryOrdinate`, which
are responsible for drawing the axes of a :class:`~gui.charting.chart.Chart`
and the associated dimension label, and for converting from values to *x* or
*y* positions and vice versa.

To access a :class:`~gui.charting.chart.Chart`'s axes, use its
:attr:`~gui.charting.chart.Chart.abscissa`,
:attr:`~gui.charting.chart.Chart.ordinate`, and
:attr:`~gui.charting.chart.Chart.secondaryOrdinate` properties.

A usage example can be found on the documentation page of the
:mod:`gui.charting` package.
"""

import abc
import math
import pango

import util


###############################################################################
# CONSTANTS                                                                   #
###############################################################################

#: The length of a major tick, in pixels. This should be an odd number.
MAJOR_TICK_LENGTH = 7

#: The length of a minor tick, in pixels. This should be an odd number.
MINOR_TICK_LENGTH = 5

#: The minimum distance between two ticks, in pixels.
MIN_TICK_DISTANCE = 7

#: The minimum distance between two tick labels on abscissae, in pixels.
ABSCISSA_MIN_TICK_LABEL_DISTANCE = 50

#: The minimum distance between two tick labels on ordinates, in pixels.
ORDINATE_MIN_TICK_LABEL_DISTANCE = 20

#: The distance between abscissae and their tick labels, in pixels.
ABSCISSA_TO_LABEL_SPACING = 5

#: The distance between the ordinates and their tick labels, in pixels.
ORDINATE_TO_LABEL_SPACING = 7

#: A tuple :samp:`({xDistance}, {yDistance})` of the distance between the end
#: of an abscissa and the top left corner of the dimension label, in pixels.
ABSCISSA_DIMENSION_LABEL_POSITION = (20, 25)

#: A tuple :samp:`({xDistance}, {yDistance})` of the distance between the end
#: of an ordinate and the bottom right corner of its dimension label, or the
#: end of a secondary ordinate and the bottom left corner of its dimension
#: label, in pixels.
ORDINATE_DIMENSION_LABEL_POSITION = (25, 20)

#: The distance the fraction bar of the dimension label exceeds the width
#: of the wider of numerator and denominator on each side, in pixels.
EXTRA_FRACTION_BAR_LENGTH = 1

#: The distance between the fraction bar of the dimension label and the
#: numerator and denominator, in pixels.
FRACTION_BAR_SPACING = 3


###############################################################################
# AXIS                                                                        #
###############################################################################

class Axis(object):
    """
    The abstract base class for the classes in this module.
    """
    __metaclass__ = abc.ABCMeta


    def __init__(self, chart):
        self._chart = chart
        self._maxValue = 1.0
        self._dimensionLabelText = None

        # The class keeps a graphics context and two Pango layouts around
        # rather than creating new ones all the time. The graphics context
        # cannot be created until the widget has been realized.
        self._graphicsContext = None
        self._tickLabelLayout = pango.Layout(chart.get_pango_context())
        self._dimensionLabelLayout = pango.Layout(chart.get_pango_context())


    @property
    def maxValue(self):
        """
        The greatest value shown on the axis. Must be at least ``0.0001``.
        """
        return self._maxValue

    @maxValue.setter
    def maxValue(self, newValue):
        # The setter for the :attr:`maxValue` property.
        if newValue < 0.0001:
            raise ValueError('maxValue must be at least 0.0001')

        self._maxValue = float(newValue)
        self._chart.queue_draw()


    @property
    def dimensionLabelText(self):
        """
        The text of the label that indicates the dimension represented on
        the axis. Strings of the form :samp:`'{numerator} / {denominator}'`
        are displayed as a proper fraction. Pango Markup Language tags
        are supported. If the value is ``None`` or ``''``, no label will
        be shown.
        """
        return self._dimensionLabelText

    @dimensionLabelText.setter
    def dimensionLabelText(self, newText):
        # The setter for the :attr:`dimensionLabelText` property.
        self._dimensionLabelText = newText
        self._chart.queue_draw()


    ###########################################################################
    # DRAWING                                                                 #
    ###########################################################################

    def draw(self):
        """
        Draws the axis on its :class:`~gui.charting.chart.Chart`.
        """
        if self._graphicsContext == None:
            self._graphicsContext = self._chart.window.new_gc()

        for value, tickLength, labelText in self._tickValues():
            self._drawTick(value, tickLength)

            if labelText != None:
                self._drawTickLabel(value, labelText)

        if bool(self._dimensionLabelText):
            self._drawDimensionLabel()


    @abc.abstractmethod
    def _drawTick(self, value, length):
        """
        Draws the tick for the given value with the given length in pixels.
        """


    def _drawTickLabel(self, value, text):
        """
        Draws the label showing the the given value at the appropriate
        position.
        """
        layout = self._tickLabelLayout
        layout.set_text(text)
        x, y = self._getTickLabelPosition(value, *layout.get_pixel_size())
        self._chart.window.draw_layout(self._graphicsContext, x, y, layout)


    def _drawDimensionLabel(self):
        """
        Draws the dimension label.
        """
        if self._dimensionLabelText.count(' / ') == 1:
            self._drawDimensionLabelFraction()
        else:
            self._drawSimpleDimensionLabel()


    def _drawSimpleDimensionLabel(self):
        """
        Draws a dimension label that consists of text, not a fraction.
        """
        layout = self._dimensionLabelLayout
        layout.set_markup(self._dimensionLabelText)
        w, h = layout.get_pixel_size()
        x, y = self._getDimensionLabelPosition(w, h)
        self._chart.window.draw_layout(self._graphicsContext, x, y, layout)


    def _drawDimensionLabelFraction(self):
        """
        Draws a dimension label that consists of a proper fraction with the
        given numerator and denominator.
        """
        window = self._chart.window
        layout = self._dimensionLabelLayout

        numerator, denominator = self._dimensionLabelText.split(' / ')

        def getInkExtends(text):
            layout.set_markup(text)
            inkExtents, logicalExtents = layout.get_pixel_extents()
            return inkExtents

        # [nd][wh] is the ink (width|height) of the (numerator|denominator).
        # [nd][xy]o is the [xy] offset of the ink rectangle of the
        # (numerator|denominator) into its logical rectangle.
        nxo, nyo, nw, nh = getInkExtends(numerator)
        dxo, dyo, dw, dh = getInkExtends(denominator)

        # f[wh] is the (width|height) of the whole fraction.
        fw = max(nw, dw) + EXTRA_FRACTION_BAR_LENGTH * 2
        fh = nh + dh + FRACTION_BAR_SPACING * 2 + 1

        # f[xy] is the [xy] position of the whole fraction.
        fx, fy = self._getDimensionLabelPosition(fw, fh)

        # [nd][xy] is the [xy] position of the (numerator|denominator).
        nx = fx + (fw - nw) // 2 - nxo
        ny = fy - nyo
        dx = fx + (fw - dw) // 2 - dxo
        dy = fy - dyo + nh + FRACTION_BAR_SPACING * 2 + 1

        # by is the y position of the fraction bar.
        by = fy + nh + FRACTION_BAR_SPACING

        window.draw_line(self._graphicsContext, fx, by, fx + fw - 1, by)
        layout.set_markup(numerator)
        window.draw_layout(self._graphicsContext, nx, ny, layout)
        layout.set_markup(denominator)
        window.draw_layout(self._graphicsContext, dx, dy, layout)


    ###########################################################################
    # UTILITY METHODS                                                         #
    ###########################################################################

    def isInBounds(self, value):
        """
        Indicates whether the given value falls within the range of values that
        are displayed on the axis.
        """
        return 0.0 <= value <= self._maxValue


    def _tickValues(self):
        """
        Returns a generator that yields tuples :samp:`({value}, {tickLength},
        {labelText})`, where `value` is the value a tick should be drawn for,
        `tickLength` is the length of that tick in pixels, and `labelText` is
        the text for the label associated with that tick, or ``None`` if that
        tick should not have a label.
        """
        length = self._getLength()

        # The number of times the distance between ticks or labels fits
        # on the axis. Need not be whole numbers since the space above the
        # last tick must be taken into account if cases where the maximum
        # value is not a multiple of the stride
        tickSlots = float(length) / MIN_TICK_DISTANCE
        labelSlots = float(length) / self._getMinTickLabelDistance()

        # The difference between the values of two major labels, chosen to
        # be the least power of 10 that does not use more lable slots than
        # available.
        stride = 10 ** math.ceil(math.log10(self.maxValue / labelSlots))

        def ticksFit(s):
            return self.maxValue / s <= tickSlots

        def labelsFit(s):
            return self.maxValue / s <= labelSlots

        assert labelsFit(stride)

        # The number of major labels, including the label at 0 (hence the +1).
        mainLabelCount = int(self.maxValue / stride) + 1

        # Determines whether to put ten minor ticks or either five or two
        # minor labels between any two major labels.
        tenthTicks = ticksFit(stride / 10)
        fifthLabels = labelsFit(stride / 5)
        halfLabels = not fifthLabels and labelsFit(stride / 2)

        # Special case: Labels at 0, 0.5, 1, 1.5, 2, ... wouldn't look right.
        if halfLabels and stride == 1 and self._maxValue >= 2.0:
            halfLabels = False

        def label(value):
            return util.stringFromFloat(value, 8, True)

        # FALLBACK: If there are no labels other than the one at zero,
        # place a label at maxValue.
        if (mainLabelCount == 1
        and (not fifthLabels or stride / 5 > self.maxValue)
        and (not halfLabels or stride / 2 > self.maxValue)):
            yield 0.0, MAJOR_TICK_LENGTH, label(0.0)
            yield self.maxValue, MAJOR_TICK_LENGTH, label(self.maxValue)
            return

        # Otherwise, yield the labels and ticks.
        for n in xrange(mainLabelCount):
            yield n * stride, MAJOR_TICK_LENGTH, label(n * stride)

            if tenthTicks or fifthLabels or halfLabels:
                for tenths in xrange(1, 10):
                    # The rounding is necessary to prevent precision issues;
                    # consider the case maxValue == 110 and stride == 100:
                    # (1 + 1 / 10.0) * 100.0 is 110.00000000000001, so the
                    # tenth tick at 110 would not be drawn without the round.
                    value = round((n + tenths / 10.0) * stride, 8)

                    if value > self.maxValue:
                        break

                    if ((halfLabels and tenths % 5 == 0)
                    or (fifthLabels and tenths % 2 == 0)):
                        yield value, MINOR_TICK_LENGTH, label(value)
                    elif tenthTicks:
                        yield value, MINOR_TICK_LENGTH, None


    @abc.abstractmethod
    def _getMinTickLabelDistance(self):
        """
        Returns the minimum distance between two tick labels. This will be
        either :data:`ABSCISSA_MIN_TICK_LABEL_DISTANCE` or
        :data:`ORDINATE_MIN_TICK_LABEL_DISTANCE`.
        """


    @abc.abstractmethod
    def _getTickLabelPosition(self, value, width, height):
        """
        Returns the position a tick label for the given value with the given
        width and height should be placed at, as a tuple :samp:`({x}, {y})`.
        """


    @abc.abstractmethod
    def _getDimensionLabelPosition(self, width, height):
        """
        Returns the position a dimension label with the given width and
        height should be placed at, as a tuple :samp:`({x}, {y})`.
        """


###############################################################################
# ABSCISSA                                                                    #
###############################################################################

class Abscissa(Axis):
    """
    Creates a new :class:`Axis` that represents an abscissa shown on the given
    :class:`~gui.charting.chart.Chart`.
    """

    def xFromValue(self, value):
        """
        Returns the *x* position the given value can be found at.
        """
        assert 0.0 <= value <= self._maxValue
        x, y, w, h = self._chart.chartArea
        return int(round(x + w * value / self._maxValue))


    def valueFromX(self, position):
        """
        Returns the value that can be found at the given *x* position.
        """
        x, y, w, h = self._chart.chartArea
        assert x <= position <= x + w
        return (float(position) - x) / w * self._maxValue


    def _getMinTickLabelDistance(self):
        # Implements the abstract method from Axis.
        return ABSCISSA_MIN_TICK_LABEL_DISTANCE


    def _drawTick(self, value, length):
        # Implements the abstract method from Axis.
        x1 = x2 = self.xFromValue(value)
        y1 = self._getY() - length // 2
        y2 = y1 + length - 1
        self._chart.window.draw_line(self._graphicsContext, x1, y1, x2, y2)


    def _getTickLabelPosition(self, value, width, height):
        # Implements the abstract method from Axis.
        x = self.xFromValue(value) - width // 2
        y = self._getY() + ABSCISSA_TO_LABEL_SPACING
        return x, y


    def _getDimensionLabelPosition(self, width, height):
        # Implements the abstract method from Axis.
        aex, aey = self._getEndX(), self._getY()
        xd, yd = ABSCISSA_DIMENSION_LABEL_POSITION
        return aex + xd, aey + yd


    def _getY(self):
        """
        Returns the *y* position of the axis.
        """
        x, y, w, h = self._chart.chartArea
        return y + h


    def _getEndX(self):
        """
        Returns the *x* position of the end of the axis.
        """
        x, y, w, h = self._chart.chartArea
        return x + w


    def _getLength(self):
        """
        Returns the length of the axis in pixels.
        """
        x, y, w, h = self._chart.chartArea
        return w


###############################################################################
# ORDINATE                                                                    #
###############################################################################

class Ordinate(Axis):
    """
    Creates a new :class:`Axis` that represents a (primary) ordinate shown on
    the given :class:`~gui.charting.chart.Chart`.
    """

    def yFromValue(self, value):
        """
        Returns the *y* position the given value can be found at.

        The method accepts values outside the range shown on the axis,
        in which case the return value is the value *y* position the
        value would be shown at of the value were in the displayed
        range, and values were shown at that position.
        """
        x, y, w, h = self._chart.chartArea
        return int(round(y + h * (1 - value / self._maxValue)))


    def valueFromY(self, position):
        """
        Returns the value that can be found at the given *y* position.
        """
        x, y, w, h = self._chart.chartArea
        assert y <= position <= y + h
        return (1 - ((float(position) - y) / h)) * self._maxValue


    def _getMinTickLabelDistance(self):
        # Implements the abstract method from Axis.
        return ORDINATE_MIN_TICK_LABEL_DISTANCE


    def _drawTick(self, value, length):
        # Implements the abstract method from Axis.
        y1 = y2 = self.yFromValue(value)
        x1 = self._getX() - length // 2
        x2 = x1 + length - 1
        self._chart.window.draw_line(self._graphicsContext, x1, y1, x2, y2)


    def _getTickLabelPosition(self, value, w, h):
        # Implements the abstract method from Axis.
        x = self._getX() - ORDINATE_TO_LABEL_SPACING - w
        y = self.yFromValue(value) - h // 2
        return x, y


    def _getDimensionLabelPosition(self, w, h):
        # Implements the abstract method from Axis.
        aex, aey = self._getX(), self._getEndY()
        xd, yd = ORDINATE_DIMENSION_LABEL_POSITION
        return aex - xd - w, aey - yd - h


    def _getX(self):
        """
        Returns the *x* position of the axis.
        """
        x, y, w, h = self._chart.chartArea
        return x


    def _getEndY(self):
        """
        Returns the *y* position of the end of the axis.
        """
        x, y, w, h = self._chart.chartArea
        return y


    def _getLength(self):
        """
        Returns the length of the axis in pixels.
        """
        x, y, w, h = self._chart.chartArea
        return h



###############################################################################
# SECONDARY ORDINATE                                                          #
###############################################################################

class SecondaryOrdinate(Ordinate):
    """
    Creates a new :class:`Ordinate` that is shown on the right side of the
    given :class:`~gui.charting.chart.Chart`, so that graphs using a
    dimension other than that of the primary ordinate can be shown.
    """

    def _getTickLabelPosition(self, value, w, h):
        # Overrides the method from Ordinate.
        x = self._getX() + ORDINATE_TO_LABEL_SPACING
        y = self.yFromValue(value) - h // 2
        return x, y


    def _getDimensionLabelPosition(self, w, h):
        # Overrides the method from Ordinate.
        aex, aey = self._getX(), self._getEndY()
        xd, yd = ORDINATE_DIMENSION_LABEL_POSITION
        return aex + xd, aey - yd - h


    def _getX(self):
        # Overrides the method from Ordinate.
        x, y, w, h = self._chart.chartArea
        return x + w

