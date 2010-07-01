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
This module contains the :class:`ParameterWidgetHandler` class, which manages
a group of widgets that allow the user to specify the :term:`heating currents
<heating current>` that are to be used for the :term:`calibration procedure`.

The top-level container of these widgets can be accessed using the handler’s
:attr:`~ParameterWidgetHandler.widget` property, and a tuple of the currents
the user has specified can be retrieved using its
:meth:`~ParameterWidgetHandler.getCurrents` method.
"""

import gtk

from gui.widgets import *
from util import gettext, ngettext


###############################################################################
# CONSTANTS                                                                   #
###############################################################################

#: Indicates whether the :class:`ParameterWidgetHandler` should emit a beep
#: the user enters an invalid value.
BEEP = True

#: The smallest legal input value for the single heating current and the
#: starting current, in mA.
MIN_CURRENT = 0.1

#: The smallest input legal value for the current increment, in mA.
MIN_CURRENT_INCREMENT = 0.1

#: The default current increment between heating stages, in mA.
DEFAULT_CURRENT_INCREMENT = 2.0

#: The maximum number of fractional digits parameters are allowed to have.
MAX_FRACTIONAL_DIGITS = 2


###############################################################################
# PARAMETER WIDGET HANDLER                                                    #
###############################################################################

class ParameterWidgetHandler(object):
    """
    Creates a new instance of this class, which allows the user to enter
    parameters for calibrating the given :class:`~ops.system.ProductionSystem`.
    """

    def __init__(self, system):
        self._system = system

        self._singleCurrent = system.heatingCurrentInSafeMode
        self._startingCurrent = system.heatingCurrentInSafeMode
        self._currentIncrement = DEFAULT_CURRENT_INCREMENT
        self._maxCurrent = system.maxHeatingCurrent

        self._createWidgets()


    @property
    def widget(self):
        """
        The top-level container of the widgets used to enter the calibration
        parameters. Immutable.
        """
        return self._widget


    def getCurrents(self):
        """
        Returns a tuple of the heating currents (in mA) for which measurements
        are to be taken during the calibration procedure.
        """
        if self._singleCurrentRadioButton.get_active():
            return (self._singleCurrent,)
        else:
            skipUsedCurrents = (self._usedCurrentsComboBox.get_active() == 0)
            usedCurrents = self._system.calibrationData.heatingCurrents
            currents = []

            currentSpan = self._maxCurrent - self._startingCurrent
            currentCount = int(currentSpan / self._currentIncrement) + 1

            for n in xrange(currentCount):
                current = self._startingCurrent + n * self._currentIncrement
                if not (skipUsedCurrents and current in usedCurrents):
                    currents.append(current)

            return tuple(currents)


    ###########################################################################
    # WIDGET CREATION                                                         #
    ###########################################################################

    def _createWidgets(self):
        """
        Creates the widgets this class is responsible for.
        """
        table = self._createParameterTable()
        self._widget = createPanel(table, yalign=0.5)


    def _createParameterTable(self):
        """
        Creates and returns the table that holds the calibration parameter
        entries and their associated labels.
        """
        table = gtk.Table(rows=6, columns=2)
        self._createSingleCurrentWidgets(table)
        self._createCurrentSeriesWidgets(table)
        table.set_col_spacing(0, LABEL_WIDGET_SPACING)
        table.set_row_spacing(0, INTER_RADIO_SPACING_COMPLICATED)
        table.set_row_spacing(1, RADIO_TO_DEPENDENTS_SPACING)
        return table


    def _createSingleCurrentWidgets(self, table):
        self._singleCurrentRadioButton = gtk.RadioButton(
            None,
            gettext('Use _a Single Heating Current'),
            use_underline=True)

        entry, box = createNumberEntryWithUnit(gettext('mA'))
        entry.set_text(str(self._singleCurrent))
        entry.connect(
            'focus-out-event', self._handleParameterChange, '_singleCurrent')
        entry.connect(
            'key-press-event', self._handleSpecialKeyPresses, '_singleCurrent')
        box.set_sensitive(False)

        table.attach(self._singleCurrentRadioButton, 0, 1, 0, 1)
        table.attach(box, 1, 2, 0, 1)

        self._singleCurrentEntry = entry
        self._singleCurrentWidgets = [box]


    def _createCurrentSeriesWidgets(self, table):
        self._currentSeriesRadioButton = gtk.RadioButton(
            self._singleCurrentRadioButton,
            gettext('Use a S_eries of Heating Currents'),
            use_underline=True)
        self._currentSeriesRadioButton.set_active(True)
        self._currentSeriesRadioButton.connect(
            'toggled', self._handleRadioToggle)

        table.attach(self._currentSeriesRadioButton, 0, 2, 1, 2)

        self._currentSeriesWidgets = []
        data = (
            (2, '_startingCurrent',  gettext('_Starting Current')),
            (3, '_currentIncrement', gettext('Current _Increment')),
            (4, '_maxCurrent',       gettext('_Maximum Current')))

        for row, name, text in data:
            entry, label, box = self._addEntyBoxLine(table, row, text)
            entry.set_text(str(getattr(self, name)))
            entry.connect(
                'focus-out-event', self._handleParameterChange, name)
            entry.connect(
                'key-press-event', self._handleSpecialKeyPresses, name)
            setattr(self, name + 'Entry', entry)
            self._currentSeriesWidgets.append(label)
            self._currentSeriesWidgets.append(box)

        self._usedCurrentsComboBox = gtk.combo_box_new_text()
        self._usedCurrentsComboBox.append_text('Skip')
        self._usedCurrentsComboBox.append_text('Replace Measurements')
        self._usedCurrentsComboBox.set_active(0)

        usedCurrentsLabel = createMnemonicLabel(self._usedCurrentsComboBox,
            '\t' + gettext('_Previously Used Currents'))

        table.attach(usedCurrentsLabel,          0, 1, 5, 6)
        table.attach(self._usedCurrentsComboBox, 1, 2, 5, 6)

        self._currentSeriesWidgets.append(usedCurrentsLabel)
        self._currentSeriesWidgets.append(self._usedCurrentsComboBox)

        return table


    def _addEntyBoxLine(self, table, row, labelText):
        entry, box = createNumberEntryWithUnit(gettext('mA'))
        label = createMnemonicLabel(entry, '\t' + labelText)

        table.attach(label, 0, 1, row, row + 1)
        table.attach(box,   1, 2, row, row + 1)

        return entry, label, box


    ###########################################################################
    # SIGNAL HANDLING                                                         #
    ###########################################################################

    def _handleSpecialKeyPresses(self, entry, event, attributeName):
        """
        Called when the user presses a key while a :class:`gtk.Entry`
        has focus. Checks whether the user pressed return (in which
        case the input is finalized) or escape (in which case the
        input is aborted). The parameter `attributeName` is the
        name of the attribute holding the last legal value of the
        given entry.
        """
        if event.keyval == gtk.gdk.keyval_from_name('Return'):
            self._handleParameterChange(entry, event, attributeName)
            entry.select_region(0, -1)   # selects the whole text
            return True
        elif event.keyval == gtk.gdk.keyval_from_name('Escape'):
            entry.set_text(str(getattr(self, attributeName)))
            entry.select_region(0, -1)   # selects the whole text
            return True
        else:
            return False


    def _handleParameterChange(self, entry, event, attributeName):
        """
        Called when an edit of the value of a :class:`gtk.Entry`
        is finalized (i.e., when it loses the focus or the user
        presses return). The parameter `attributeName` is the
        name of the attribute holding the last legal value of the
        given entry.
        """
        self._checkEntryValue(entry, attributeName)
        return False


    def _checkEntryValue(self, entry, attributeName):
        """
        Checks whether the value of the given :class:`gtk.Entry` is valid. If
        the value is out of range, it is are replaced with the closest valid
        value. If it is non-numeric, it is replaced by the last legal value.
        The parameter `attributeName` is the name of the attribute holding
        the last legal value of the given entry.
        """
        ok = True

        try:
            value = float(entry.get_text())
        except ValueError:
            fixedValue = getattr(self, attributeName)
            ok = False
        else:
            limits = {
                '_singleCurrent':
                    (MIN_CURRENT, self._system.maxHeatingCurrent),
                '_startingCurrent':
                    (MIN_CURRENT, self._maxCurrent),
                '_currentIncrement':
                    (MIN_CURRENT_INCREMENT, None),
                '_maxCurrent':
                    (self._startingCurrent, self._system.maxHeatingCurrent)}

            fixedValue = util.limit(value, *limits[attributeName])

            if value != fixedValue:
                ok = False

            fixedValue = round(fixedValue, MAX_FRACTIONAL_DIGITS)

        if not ok and BEEP:
            gtk.gdk.beep()

        # Set the entry text even if the input was fine to normalize it.
        entry.set_text(str(fixedValue))
        setattr(self, attributeName, fixedValue)

        return ok


    def _handleRadioToggle(self, radioButton):
        series = radioButton.get_active()
        for widget in self._singleCurrentWidgets:
            widget.set_sensitive(not series)
        for widget in self._currentSeriesWidgets:
            widget.set_sensitive(series)



