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
This module contains the :class:`ChartHandler` class, which manages a set of
:class:`~gui.charting.chart.Chart` widgtes that visualize the measurements
taken during the :term:`calibration procedure` and the and the
:term:`estimation functions <estimation function>` that are its result.

The class provides three charts:

* the *measurements chart*, which shows the :term:`temperature measurements
  <temperature measurement>` the user has taken for the :term:`heating
  currents <heating current>` used during the calibration procedure and
  the :term:`temperature sensor voltages <temperature sensor voltage>`
  at the time the measurements were taken;

* the *temperature chart*, which plots the function used to estimate the
  :term:`heating temperature` that corresponds to a given :term:`temperature
  sensor voltage`; and

* the *current chart*, which plots the function used to estimate the
  :term:`heating current` that needs to be used to heat the system to a given
  :term:`target temperature`.

Clients need not actually deal with the :class:`ChartHandler`
itself; instead, they can use the :func:`createCharts` function,
which creates the handler and returns the :class:`~gui.charting.chart.Chart`
widgtes. The charts will be automatically updated when the
calibration data of the :class:`~ops.system.ProductionSystem` passed to
the function changes.

|

.. image:: measurements-chart.png
    :align: center

|
"""

from gui.charting.chart import Chart
from gui.charting.graph import FunctionGraph, PointGraph

import ops.event
import ops.calibration.event
from util import gettext, parseOrDefault


def createCharts(system):
    """
    Creates a :class:`ChartHandler` and returns its
    :class:`~gui.charting.chart.Chart` widgets as a tuple
    :samp:`({measurementsChart}, {temperatureChart}, {currentChart})`.
    `system` is the :class:`~ops.system.ProductionSystem` whose calibration
    measurement are to be visualized.
    """
    handler = ChartHandler(system)
    return (
        handler.measurementsChart,
        handler.temperatureChart,
        handler.currentChart)


###############################################################################
# CONSTANTS                                                                   #
###############################################################################

#: The minimum size of the charts in pixels, as a tuple
#: :samp:`({width}, {height})`.
CHART_SIZE = (400, 330)

#: A tuple that lists the text of the dimension labels for heating current,
#: heating temperature, and temperature sensor voltage. Strings of the form
#: :samp:`'{numerator} / {denominator}'` are displayed as a proper fraction.
#: Pango Markup Language tags are supported.
DIMENSION_LABEL_TEXTS = (
    gettext('<i>I</i> / mA'),
    gettext('<i>T</i> / °C'),
    gettext('<i>U</i> / V'))

#: A tuple that lists the colors used for the graphs that show heating
#: current, heating temperature, and temperature sensor voltage, as
#: X11 color names (e.g. ``'blanched almond'``) or hexadecimal strings
#: (e.g. ``'#FFEBCD'``).
#:
#: If these colors are changed, the captions need to be adjusted as well.
COLORS = ('orange', 'red', 'blue')

#: A tuple of the captions used for the measurements chart, temperature chart,
#: and current chart if the estimation function could be fitted.
#: Pango Markup Language tags are supported.
COMPLETE_CAPTIONS = (
    gettext('Shown are the final heating temperatures (red squares) and '
    'temperature sensor voltages (blue diamonds) measured for the given '
    'heating currents, and the estimation function for the final heating '
    'temperature (red curve).'),
    gettext('Shown are the heating temperatures measured for the given '
    'temperature sensor voltages (red squares) and the estimation '
    'function for the heating temperature (red curve).'),
    gettext('Shown are the heating currents used to reach the given '
    'temperatures (orange squares) and the estimation function for the '
    'heating current (orange curve).'))

#: A tuple of the captions used for the measurements chart, temperature chart,
#: and current chart if the estimation function could not be fitted.
#: Pango Markup Language tags are supported.
INCOMPLETE_CAPTIONS = (
    gettext('Shown are the final heating temperatures (red squares) and '
    'temperature sensor voltages (blue diamonds) measured for the given '
    'heating currents.'),
    gettext('Shown are the heating temperatures measured for the given '
    'temperature sensor voltages (red squares).'),
    gettext('Shown are the heating currents used to reach the given '
    'temperatures (orange squares).'))

#: The minimum number of lines worth of space the charts reserve for their
#: caption. If a captions uses fewer lines, it still receives the amount
#: of vertical space that would be used by that number of lines, so that
#: the charts are visually congruent. If a caption uses more lines, it
#: receives as much space as required.
#:
#: The value can be set during localization by using a message string that
#: can be parsed as an integer for the message id ``{{MIN_CAPTION_LINES}}``.
MIN_CAPTION_LINES = parseOrDefault(gettext('{{MIN_CAPTION_LINES}}'), int, 3)


###############################################################################
# CHART HANDLER                                                               #
###############################################################################

class ChartHandler(object):
    """
    Creates a new instance of this class, which visualizes the calibration
    data of the given :class:`~ops.system.ProductionSystem`.
    """

    def __init__(self, system):
        system.mediator.addListener(self._calibrationDataChangedListener,
            ops.calibration.event.CalibrationDataChanged)
        system.mediator.addListener(self._systemPropertiesChangedListener,
            ops.event.SystemPropertiesChanged)

        self._createWidgets(system)

        self._updateAxes(system)
        self._updateGraphs(system.calibrationData)


    @property
    def measurementsChart(self):
        """
        The :class:`~gui.charting.chart.Chart` object that displays the
        measurements chart. Immutable.
        """
        return self._measurementsChart


    @property
    def temperatureChart(self):
        """
        The :class:`~gui.charting.chart.Chart` object that displays the
        temperature chart. Immutable.
        """
        return self._temperatureChart


    @property
    def currentChart(self):
        """
        The :class:`~gui.charting.chart.Chart` object that displays the
        current chart. Immutable.
        """
        return self._currentChart


    ###########################################################################
    # WIDGET CREATION                                                         #
    ###########################################################################

    def _createWidgets(self, system):
        """
        Creates the widgets this class is responsible for.
        """
        def doCreate(abscissaText, ordinateText, secondaryOrdinateText):
            chart = Chart()
            chart.minCaptionLines = MIN_CAPTION_LINES
            chart.set_size_request(*CHART_SIZE)
            chart.abscissa.dimensionLabelText = abscissaText
            chart.ordinate.dimensionLabelText = ordinateText
            chart.secondaryOrdinate.dimensionLabelText = secondaryOrdinateText
            return chart

        iText, tText, uText = DIMENSION_LABEL_TEXTS

        self._measurementsChart = doCreate(iText, tText, uText)
        self._temperatureChart  = doCreate(uText, tText, None)
        self._currentChart      = doCreate(tText, iText, None)

        self._measurementsChart.showSecondaryOrdinate = True


    ###########################################################################
    # UPDATE HANDLING                                                         #
    ###########################################################################

    def _systemPropertiesChangedListener(self, event):
        """
        Called when a :class:`~ops.calibration.event.SystemPropertiesChanged`
        event is sent. Updates the maxValues of the charts' axes.
        """
        self._updateAxes(event.system)


    def _updateAxes(self, system):
        """
        Updates the max values of the charts' axes with values retrieved
        from the given production system.
        """
        def doUpdate(chart, abscissaMax, ordinateMax, secondaryOrdinateMax):
            chart.abscissa.maxValue = abscissaMax
            chart.ordinate.maxValue = ordinateMax
            if secondaryOrdinateMax != None:
                chart.secondaryOrdinate.maxValue = secondaryOrdinateMax

        maxValues = (
            system.maxHeatingCurrent,
            system.maxSafeTemperature,
            system.maxSafeTemperatureSensorVoltage)

        maxI, maxT, maxU = maxValues

        doUpdate(self.measurementsChart, maxI, maxT, maxU)
        doUpdate(self.temperatureChart,  maxU, maxT, None)
        doUpdate(self.currentChart,      maxT, maxI, None)


    def _calibrationDataChangedListener(self, event):
        """
        Called when a :class:`~ops.calibration.event.CalibrationDataChanged`
        event is sent. Updates the charts' graphs.
        """
        self._updateGraphs(event.calibrationData)


    def _updateGraphs(self, cd):
        """
        Clears the charts' graphs, then creates new ones from the given
        calibration data object. Also adjusts the charts' captions depending
        on whether the calibration data is complete.
        """
        self.measurementsChart.clearGraphs()
        self.temperatureChart.clearGraphs()
        self.currentChart.clearGraphs()

        captions = INCOMPLETE_CAPTIONS

        if cd.hasMeasurements:
            itPoints = zip(cd.heatingCurrents, cd.temperatures)
            iuPoints = zip(cd.heatingCurrents, cd.temperatureSensorVoltages)
            utPoints = zip(cd.temperatureSensorVoltages, cd.temperatures)
            tiPoints = zip(cd.temperatures, cd.heatingCurrents)

            iColor, tColor, uColor = COLORS

            self.measurementsChart.addGraph(PointGraph(itPoints, tColor))
            self.temperatureChart.addGraph(PointGraph(utPoints, tColor))
            self.currentChart.addGraph(PointGraph(tiPoints, iColor))

            self.measurementsChart.addSecondaryGraph(
                PointGraph(iuPoints, uColor, style='diamonds'))

            if cd.isComplete:
                self.measurementsChart.addGraph(FunctionGraph(
                    cd.getFinalTemperatureFromCurrent, tColor, False))
                self.temperatureChart.addGraph(FunctionGraph(
                    cd.getTemperatureFromVoltage, tColor, False))
                self.currentChart.addGraph(FunctionGraph(
                    cd.getCurrentFromTargetTemperature, iColor, False))

                captions = COMPLETE_CAPTIONS

        self.measurementsChart.captionText = captions[0]
        self.temperatureChart.captionText = captions[1]
        self.currentChart.captionText = captions[2]
