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
This module contains the :class:`FunctionWidgetHandler` class, which manages
a group of widgets that display the :term:`estimation functions
<estimation function>` that have been fitted during the :term:`calibration
procedure`. If the functions haven't been fitted yet, a label that states
this is shown instead.

Clients need not actually deal with the :class:`FunctionWidgetHandler` itself;
instead, they can use the :func:`createFunctionWidgets` function, which creates
the handler and returns the top-level container of the widgets used to show the
functions. The functions will be automatically updated when the calibration
data of the :class:`~ops.system.ProductionSystem` passed to the function
changes.

|

.. image:: functions.png
    :align: center

|
"""

import gtk

from gui.widgets import createPanel
from ops.calibration.event import CalibrationDataChanged
from util import gettext


def createFunctionWidgets(system):
    """
    Creates a :class:`FunctionWidgetHandler` and returns the top-level
    container of the widgets used to show the functions. `system` is the
    :class:`~ops.system.ProductionSystem` whose estimation functions
    are to be shown.
    """
    return FunctionWidgetHandler(system).widget


###############################################################################
# CONSTANTS                                                                   #
###############################################################################

#: The amount of empty space used between a function's caption and the
#: function itself, in pixels.
CAPTION_TO_FUNCTION_SPACING = 3

#: The amount of empty space used between a function and the caption for the
#: next function, in pixels.
FUNCTION_TO_CAPTION_SPACING = 18


###############################################################################
# FUNCTION WIDGET HANDLER                                                     #
###############################################################################

class FunctionWidgetHandler(object):
    """
    Creates a new instance of this class, which shows the estimation functions
    fitted for the given :class:`~ops.system.ProductionSystem`.
    """

    def __init__(self, system):
        system.mediator.addListener(self._handleUpdate, CalibrationDataChanged)
        self._createWidgets()
        self._updateWidgets(system.calibrationData)


    @property
    def widget(self):
        """
        The top-level container of the widgets that show the estimation
        functions. Immutable.
        """
        return self._widget


    # The names of the estimation functions.
    FUNCTIONS = (
        'currentFromTargetTemperature',
        'finalTemperatureFromCurrent',
        'temperatureFromVoltage')


    ###########################################################################
    # WIDGET CREATION                                                         #
    ###########################################################################

    def _createWidgets(self):
        """
        Creates the widgets this class is responsible for.
        """
        widgets = (
            self._createFunctionTable(),
            gtk.Label(gettext('The production system is not calibrated.')))

        self._widget = createPanel(*widgets, yalign=0.5, xscale=1.0)
        self._widget.show_all()

        # The widget needs to have a reference to this instance to prevent it
        # from being reclaimed as garbage while the widget is still alive.
        self._widget.functionWidgetHandler = self

        for w in widgets:
            w.set_no_show_all(True)

        self._functionTable, self._notCalibratedLabel = widgets


    def _createFunctionTable(self):
        """
        Creates the :class:`gtk.Table` that holds the functions.

        The functions themselves are broken across two labels each: the name
        label, which shows the 'f(x) = ' part, and the function label, which
        shows the body of the function. This ensures proper line breaking, and
        makes it easier to have the equal signs line up. Since the function
        label contains superscripts and is thus unusually high, it is necessary
        to nudge the name label a couple of pixels down, so that the labels'
        baselines align. See :meth:`_adjustNameLabelPosition`.
        """
        table = gtk.Table(rows=6, columns=2)

        captions = (
            gettext('Heating Current from Target Temperature:'),
            gettext('Final Temperature from Heating Current:'),
            gettext('Heating Temperature from Temperature Sensor Voltage:'))

        functionNames = (
            gettext('<i>I</i>(<i>T</i>)'),
            gettext('<i>T</i>(<i>I</i>)'),
            gettext('<i>T</i>(<i>U</i>)'))

        # Each function takes up two rows, which are arranged as follows.
        #                 0                       1
        #     +-----------------------------------------------+
        #     | captionLabel                                  |  top
        #     +-----------------------+-----------------------+
        #     |    nameLabelAlignment | functionLabel         |  bottom
        #     +-----------------------+-----------------------+

        for i in xrange(3):
            captionLabel = gtk.Label(captions[i])
            captionLabel.set_alignment(0.0, 0.0)

            nameLabel = gtk.Label()
            nameLabel.set_markup('\t%s = ' % functionNames[i])

            # Used for nudging the lable down by setting setting the padding,
            # which is done later.
            nameLabelAlignment = gtk.Alignment(xalign=1.0, xscale=0.0)
            nameLabelAlignment.add(nameLabel)

            functionLabel = gtk.Label()
            functionLabel.set_alignment(0.0, 0.0)
            functionLabel.set_line_wrap(True)

            prefix = '_' + self.FUNCTIONS[i]
            setattr(self, prefix + 'NameLabel', nameLabel)
            setattr(self, prefix + 'NameLabelAlignment', nameLabelAlignment)
            setattr(self, prefix + 'FunctionLabel', functionLabel)

            top, bottom, next = 0+2*i, 1+2*i, 2+2*i

            table.attach(captionLabel,       0, 2, top,    bottom)
            table.attach(nameLabelAlignment, 0, 1, bottom, next)
            table.attach(functionLabel,      1, 2, bottom, next)

            table.set_row_spacing(top,    CAPTION_TO_FUNCTION_SPACING)
            table.set_row_spacing(bottom, FUNCTION_TO_CAPTION_SPACING)

        return table


    ###########################################################################
    # UPDATE HANDLING                                                         #
    ###########################################################################

    def _handleUpdate(self, event):
        """
        Called when a :class:`~ops.calibration.event.CalibrationDataChanged`
        event is sent. Updates the widgets.
        """
        self._updateWidgets(event.calibrationData)


    def _updateWidgets(self, calibrationData):
        """
        Updates the widgets. If the calibration data is complete, the table
        containing the functions is shown. Otherwise, a label that explains
        that the system isn't calibrated is shown.
        """
        if calibrationData.isComplete:
            self._functionTable.show()
            self._notCalibratedLabel.hide()
            self._updateTable(calibrationData)
        else:
            self._functionTable.hide()
            self._notCalibratedLabel.show()


    def _updateTable(self, calibrationData):
        """
        Updates the table containing the functions. `calibrationData` needs to
        be complete.
        """
        variables = (
            gettext('<i>T</i>'), gettext('<i>I</i>'), gettext('<i>U</i>'))

        for i in xrange(3):
            prefix = '_' + self.FUNCTIONS[i]
            nameLabel = getattr(self, prefix + 'NameLabel')
            alignment = getattr(self, prefix + 'NameLabelAlignment')
            functionLabel = getattr(self, prefix + 'FunctionLabel')

            c = getattr(calibrationData, self.FUNCTIONS[i] + 'Coefficients')
            functionLabel.set_markup(self._formatPolynomial(c, variables[i]))

            self._adjustNameLabelPosition(nameLabel, alignment, functionLabel)


    def _adjustNameLabelPosition(self, nameLabel, alignment, functionLabel):
        """
        Adjusts `nameLabel`'s position so that its baseline properly aligns
        with that of `functionLabel`. `alignment` is the :class:`gtk.Alignment`
        the `nameLabel' is in.
        """
        functionLabelBase = self._getFirstBaselinePosition(functionLabel)
        nameLabelBase = self._getFirstBaselinePosition(nameLabel)
        nudge = max(0, functionLabelBase - nameLabelBase)
        alignment.set_padding(nudge, 0, 0, 0)


    def _getFirstBaselinePosition(self, label):
        """
        Returns the distance from the top of the given :class:`gtk.Label` to
        the baseline of its first line, in pixels.
        """
        return -label.get_layout().get_line(0).get_pixel_extents()[1][1]


    ###########################################################################
    # POLYNOMIAL FORMATTING                                                   #
    ###########################################################################

    def _formatPolynomial(self, coefficients, x):
        """
        Formats a polynomial with the given coefficients as a Pango Markup
        Language string. Uses non-breaking whitespace to prevent improper
        line breaking. `x` is used as the variable.
        """
        result = u''
        powers = reversed(xrange(len(coefficients)))

        for coefficient, power in zip(coefficients, powers):
            if coefficient == 0.0:
                continue

            if result == '':
                result += MINUS + WJ     if coefficient < 0   else u''
            else:
                result += ' '
                result += MINUS + NBSP   if coefficient < 0   else PLUS + NBSP

            result += self._formatNumber(abs(coefficient))

            if power == 1:
                result += NBSP + x
            if power > 1:
                result += NBSP + x + WJ + u'<sup>' + unicode(power) + u'</sup>'

        return result


    def _formatNumber(self, n):
        """
        Formats a floating-point number as a Pango Markup Language string,
        using proper scientific notation rather e notation. Uses non-breaking
        whitespace to prevent improper line breaking
        """
        parts = (u'%.4g' % n).split(u'e')

        if len(parts) == 1:
            return parts[0]
        else:
            m, e = parts
            result =  m + NBSP + TIMES + NBSP + u'10' + WJ + u'<sup>'
            if e[0] == u'-':
                result += MINUS + WJ + e.lstrip(u'-0')
            else:
                result += e.lstrip(u'+0')
            result += u'</sup>'
            return result


###############################################################################
# SPECIAL CHARACTERS                                                          #
###############################################################################

WJ    = u'\u2060'   # The word joiner, aka zero-width non-breaking space.
NBSP  = u'\u00A0'   # The non-breaking space.
PLUS  = u'+'
MINUS = u'\u2212'
TIMES = u'\u00D7'
