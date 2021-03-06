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
from ops.event import SystemPropertiesChanged
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

        self._singleCurrent = system.heatingCurrentWhileIdle
        self._startingCurrent = system.heatingCurrentWhileIdle
        self._currentIncrement = DEFAULT_CURRENT_INCREMENT
        self._maxCurrent = system.maxHeatingCurrent

        system.mediator.addListener(
            self._handleSystemPropertiesChange, SystemPropertiesChanged)

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
        """
        Creates the radio button for single current mode and the entry for the
        current and adds them to the given table.
        """
        self._singleCurrentRadioButton = gtk.RadioButton(
            None,
            gettext('Use _a Single Heating Current'),
            use_underline=True)
        # The signal handler is connected to the current series radio button.

        entry, box = createNumberEntryWithUnit(gettext('mA'))
        entry.set_text(str(self._singleCurrent))
        entry.connect(
            'focus-out-event', self._handleFocusOutEvent, '_singleCurrent')
        entry.connect(
            'key-press-event', self._handleSpecialKeyPresses, '_singleCurrent')
        box.set_sensitive(False)

        table.attach(
            alignLeft(self._singleCurrentRadioButton), 0, 1, 0, 1, yoptions=0)
        table.attach(box, 1, 2, 0, 1)

        self._singleCurrentEntry = entry
        self._singleCurrentWidgets = [box]


    def _createCurrentSeriesWidgets(self, table):
        """
        Creates the radio button for current series mode and the various
        widgets used to specify the current series, and adds them to the
        given table.
        """
        self._currentSeriesWidgets = []
        self._createCurrentSeriesRadioButton(table)
        self._createCurrentSeriesEntries(table)
        self._createUsedCurrentsComboBox(table)


    def _createCurrentSeriesRadioButton(self, table):
        """
        Creates the radio button for current series mode and adds it to the
        given table.
        """
        self._currentSeriesRadioButton = gtk.RadioButton(
            self._singleCurrentRadioButton,
            gettext('Use a S_eries of Heating Currents'),
            use_underline=True)
        self._currentSeriesRadioButton.set_active(True)
        self._currentSeriesRadioButton.connect(
            'toggled', self._handleRadioToggle)

        table.attach(alignLeft(self._currentSeriesRadioButton), 0, 2, 1, 2)


    def _createCurrentSeriesEntries(self, table):
        """
        Creates the entry widgets used to specify the current series and the
        associated labels, and adds them to the given table.
        """
        data = (
            (2, '_startingCurrent',  gettext('_Starting Current')),
            (3, '_currentIncrement', gettext('Current _Increment')),
            (4, '_maxCurrent',       gettext('_Maximum Current')))

        for row, name, labelText in data:
            entry, box = createNumberEntryWithUnit(gettext('mA'))

            entry.set_text(str(getattr(self, name)))
            entry.connect(
                'focus-out-event', self._handleFocusOutEvent, name)
            entry.connect(
                'key-press-event', self._handleSpecialKeyPresses, name)
            setattr(self, name + 'Entry', entry)

            label = createMnemonicLabel(entry, '\t' + labelText)

            table.attach(label, 0, 1, row, row + 1)
            table.attach(box,   1, 2, row, row + 1)

            self._currentSeriesWidgets.append(label)
            self._currentSeriesWidgets.append(box)


    def _createUsedCurrentsComboBox(self, table):
        """
        Creates the combo box used to specify whether currents with existing
        measurements should be skipped and the associated label, and adds
        them to the given table.
        """
        self._usedCurrentsComboBox = gtk.combo_box_new_text()
        self._usedCurrentsComboBox.append_text('Skip')
        self._usedCurrentsComboBox.append_text('Replace Measurements')
        self._usedCurrentsComboBox.set_active(0)

        usedCurrentsLabel = createMnemonicLabel(
            self._usedCurrentsComboBox,
            '\t' + gettext('_Previously Used Currents'))

        table.attach(usedCurrentsLabel,          0, 1, 5, 6)
        table.attach(self._usedCurrentsComboBox, 1, 2, 5, 6)

        self._currentSeriesWidgets.append(usedCurrentsLabel)
        self._currentSeriesWidgets.append(self._usedCurrentsComboBox)


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
            self._finalizeInput(entry, attributeName)
            entry.select_region(0, -1)   # selects the whole text
            return True
        elif event.keyval == gtk.gdk.keyval_from_name('Escape'):
            entry.set_text(str(getattr(self, attributeName)))
            entry.select_region(0, -1)   # selects the whole text
            return True
        else:
            return False


    def _handleFocusOutEvent(self, entry, event, attributeName):
        """
        Called when a :class:`gtk.Entry` loses the focus. Finalizes the input.
        """
        self._finalizeInput(entry, attributeName)
        return False


    def _finalizeInput(self, entry, attributeName):
        """
        Stores the value entered into the given :class:`gtk.Entry` in the
        instance attribute with the given name. If the value is out of range,
        it is replaced with the closest valid value first. If it isn't a
        number, it is replaced with the value of the attribute instead.
        """
        ok = True

        try:
            value = float(entry.get_text())
        except ValueError:
            fixedValue = getattr(self, attributeName)
            ok = False
        else:
            iMaxSystem = self._system.maxHeatingCurrent
            limits = {
                '_singleCurrent':    (MIN_CURRENT, iMaxSystem),
                '_startingCurrent':  (MIN_CURRENT, self._maxCurrent),
                '_currentIncrement': (MIN_CURRENT_INCREMENT, None),
                '_maxCurrent':       (self._startingCurrent, iMaxSystem)}

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
        """
        Called when :attr:`_currentSeriesRadioButton` is activated or
        deactivated. Activates the current series widgets and deactivates
        the single current widgets, or vice versa.
        """
        assert radioButton == self._currentSeriesRadioButton
        series = radioButton.get_active()
        for widget in self._singleCurrentWidgets:
            widget.set_sensitive(not series)
        for widget in self._currentSeriesWidgets:
            widget.set_sensitive(series)


    def _handleSystemPropertiesChange(self, event):
        """
        Called when a property of :attr:`_system` changes. If the changed
        property is :attr:`~ops.system.ProductionSystem.maxHeatingCurrent`,
        ensures that :attr:`_singleCurrent`, :attr:`_startingCurrent`, and
        :attr:`_maxCurrent` are still legal.
        """
        if event.name == 'maxHeatingCurrent':
            iMax = self._system.maxHeatingCurrent

            for name in ('_singleCurrent', '_startingCurrent', '_maxCurrent'):
                if getattr(self, name) > iMax:
                    setattr(self, name, iMax)
                    getattr(self, name + 'Entry').set_text(str(iMax))

