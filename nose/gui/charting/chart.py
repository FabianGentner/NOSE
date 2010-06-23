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
This module contains the :class:`Chart` class, which is a :class:`gtk.Widget`
that draws simple charts. Most of the actual work is performed by the classes
in the :mod:`gui.charting.axis` and :mod:`gui.charting.graph` modules.

A list of the features charts provide and a usage example can be
found on the documentation page of the :mod:`gui.charting` package.
"""

import collections
import gtk
import pango

from util import gettext, ApplicationError
from gui.widgets import getColor

import gui.charting.axis
import gui.charting.graph


###############################################################################
# NAMED TUPLES                                                                #
###############################################################################

Area = collections.namedtuple('Area', 'x y width height')
Border = collections.namedtuple('Border', 'top bottom left right')


###############################################################################
# CONSTANTS                                                                   #
###############################################################################

#: A string that is drawn in the middle of the chart area if there are no
#: graphs to be drawn. Pango Markup Language tags are supported.
NO_DATA_TEXT = gettext('no data available')

#: A named tuple :samp:`({top}, {bottom}, {left}, {right})` of the amount of
#: space left around the actual chart for showing the axes' tick and dimension
#: labels. :samp:`{bottom}` does not include the space for the caption.
BORDER = Border(top=60, bottom=60, left=60, right=60)


###############################################################################
# THE CHART CLASS                                                            #
###############################################################################

class Chart(gtk.DrawingArea):
    """
    Creates a new instance of this class. :class:`Chart` is a subclass of
    :class:`gtk.DrawingArea`.
    """

    def __init__(self):
        super(self.__class__, self).__init__()

        self.connect('expose_event', self._draw)
        self.connect('size-allocate', self._updateChartArea)

        self._abscissa = gui.charting.axis.Abscissa(self)
        self._ordinate = gui.charting.axis.Ordinate(self)
        self._secondaryOrdinate = gui.charting.axis.SecondaryOrdinate(self)

        self._showSecondaryOrdinate = False

        self._graphs = []

        self._captionText = None
        self._minCaptionLines = 0

        self._chartArea = None

        # The class keeps a number of graphics contexts and Pango layouts
        # around rather than creating new ones all the time. The graphics
        # contexts cannot be created until the widget has been realized.
        self._foregroundGC = None
        self._backgroundGC = None

        self._noDataLabelLayout = pango.Layout(self.get_pango_context())

        self._captionLayout = pango.Layout(self.get_pango_context())
        self._captionLayout.set_wrap(pango.WRAP_WORD)
        self._captionLayout.set_alignment(pango.ALIGN_CENTER)


    ###########################################################################
    # AXES                                                                    #
    ###########################################################################

    @property
    def abscissa(self):
        """The chart's :class:`~gui.charting.axis.Abscissa`. Read-only."""
        return self._abscissa


    @property
    def ordinate(self):
        """The chart's :class:`~gui.charting.axis.Ordinate`. Read-only."""
        return self._ordinate


    @property
    def secondaryOrdinate(self):
        """
        The chart's :class:`~gui.charting.axis.SecondaryOrdinate`. Read-only.
        The secondary ordinate is only shown if :attr:`showSecondaryOrdinate`
        is set to ``True``.
        """
        return self._secondaryOrdinate


    @property
    def showSecondaryOrdinate(self):
        """
        Determines whether the chart's secondary ordinate will be shown. May
        be modified. The default is ``False``.
        """
        return self._showSecondaryOrdinate

    @showSecondaryOrdinate.setter
    def showSecondaryOrdinate(self, newValue):
        # The setter for the :attr:`showSecondaryOrdinate` property.
        self._showSecondaryOrdinate = newValue
        self.queue_draw()


    ###########################################################################
    # GRAPHS                                                                  #
    ###########################################################################

    def addGraph(self, graph):
        """
        Adds the given graph to those that are displayed on chart. A chart can
        have any number of graphs, and a graph can be shown on any number of
        charts.
        """
        self._graphs.append((graph, self.ordinate))
        self.queue_draw()


    def addSecondaryGraph(self, graph):
        """
        Adds the given graph to those that are displayed on chart. The graph
        will use the dimension of the secondary ordinate.
        If :attr:`showSecondaryOrdinate` is ``False``, the graph will not be
        shown.

        A chart can have any number of graphs, and a graph can be shown on any
        number of charts.
        """
        self._graphs.append((graph, self.secondaryOrdinate))
        self.queue_draw()


    def clearGraphs(self):
        """
        Removes all graphs from the chart.
        """
        del self._graphs[:]
        self.queue_draw()


    ###########################################################################
    # CAPTION                                                                 #
    ###########################################################################

    @property
    def captionText(self):
        """
        The text of the chart's caption. Pango Markup Language tags are
        supported. The caption is only shown if the chart has at least
        one graph. If the value is ``None`` or ``''``, no caption will
        be shown.
        """
        return self._captionText

    @captionText.setter
    def captionText(self, newText):
        # The setter for the :attr:`captionText` property.
        self._captionText = newText
        self._updateChartArea()
        self.queue_draw()


    @property
    def minCaptionLines(self):
        """
        The minimum number of lines worth of space the chart reserves for
        its caption. If the captions uses fewer lines, it still receives the
        amount of vertical space that would be used by that number of lines.
        If a caption uses more lines, it receives as much space as required.

        This is useful to give a series of related charts with captions of
        different lengths an uniform appearance.
        """
        return self._minCaptionLines

    @minCaptionLines.setter
    def minCaptionLines(self, newValue):
        # The setter for the :attr:`minCaptionLines` property.
        if newValue < 0:
            raise ApplicationError('minCaptionLines must not be negative')
        else:
            self._minCaptionLines = newValue
            self._updateChartArea()
            self.queue_draw()


    ###########################################################################
    # CHART AREA                                                              #
    ###########################################################################

    @property
    def chartArea(self):
        """
        A named tuple :samp:`({x}, {y}, {width}, {height})` that indicates the
        position and size of the area of the widget used to show the actual
        chart rather than the tick labels, the dimension labels, and the
        caption. Read-only.

        The tuple is automatically updated when :attr:`captionText`,
        :attr:`minCaptionLines` or the widget's size allocation change.
        """
        return self._chartArea


    def _updateChartArea(self, *parameters):
        """
        Recalculates :attr:`chartArea`. Called when :attr:`captionText`,
        :attr:`minCaptionLines`, or the widget's size allocation change.
        In the latter case, GTK calls this method with a number of
        parameters, which are ignored.
        """
        if self.minCaptionLines > 0:
            self._captionLayout.set_markup('\n' * (self.minCaptionLines - 1))
            minHeight = self._captionLayout.get_pixel_size()[1]
        else:
            minHeight = 0

        if bool(self.captionText):
            self._captionLayout.set_markup(self.captionText)
            self._captionLayout.set_width(self.allocation.width * pango.SCALE)
            actualHeight = self._captionLayout.get_pixel_size()[1]
        else:
            actualHeight = 0

        captionHeight = max(minHeight, actualHeight)

        x = self.allocation.x + BORDER.left
        y = self.allocation.y + BORDER.top
        w = self.allocation.width - BORDER.left - BORDER.right
        h = self.allocation.height - BORDER.top - BORDER.bottom - captionHeight

        self._chartArea = Area(x, y, w, h)


    ###########################################################################
    # DRAWING                                                                 #
    ###########################################################################

    def _draw(self, *parameters):
        """
        Draws the chart. GTK calls this method with a number of parameters,
        which are ignored.
        """
        if self._foregroundGC == None or self._backgroundGC == None:
            self._createGraphicsContexts()

        self._drawBackground()
        self._drawChartAreaRectangle()
        self._drawCaption()
        self._drawAxes()

        if len(self._graphs) > 0:
            self._drawGraphs()
        else:
            self._drawNoDataText()


    def _createGraphicsContexts(self):
        """
        Creates the graphics contexts used by this class.
        This is not possible until the widget has been realized.
        """
        self._foregroundGC = self.window.new_gc()
        self._backgroundGC = self.window.new_gc()
        self._backgroundGC.foreground = getColor('white')


    def _drawBackground(self):
        """
        Draws the background.
        """
        self.window.draw_rectangle(self._backgroundGC, True, *self.allocation)


    def _drawChartAreaRectangle(self):
        """
        Draws the rectangle around the chart area.
        """
        self.window.draw_rectangle(self._foregroundGC, False, *self.chartArea)


    def _drawCaption(self):
        """
        Draws the chart's caption.
        """
        if bool(self.captionText) and len(self._graphs) > 0:
            self.window.draw_layout(
                self._foregroundGC,
                0, self.chartArea.height + BORDER.top + BORDER.bottom,
                self._captionLayout)


    def _drawAxes(self):
        """
        Draws the chart's axes.
        """
        self.abscissa.draw()
        self.ordinate.draw()

        if self.showSecondaryOrdinate:
            self.secondaryOrdinate.draw()


    def _drawGraphs(self):
        """
        Draws the graphs that have been added to the chart.
        """
        for graph, ordinate in self._graphs:
            if self.showSecondaryOrdinate or ordinate is self.ordinate:
                graph.draw(self, self.abscissa, ordinate)


    def _drawNoDataText(self):
        """
        Draws the no data message.
        """
        if bool(NO_DATA_TEXT):
            self._noDataLabelLayout.set_markup(NO_DATA_TEXT)
            tw, th = self._noDataLabelLayout.get_pixel_size()
            cax, cay, caw, cah = self.chartArea
            self.window.draw_layout(
                self._foregroundGC,
                cax + (caw - tw) // 2,
                cay + (cah - th) // 2,
                self._noDataLabelLayout)
