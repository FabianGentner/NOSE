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

from gui.widgets import *
from util import gettext, limit


#: Indicates whether the :class:`SystemPropertiesDialogHandler` should emit
#: a beep the user enters an invalid value.
BEEP = True

DATA = (
    (gettext('Heating _Current'), gettext('mA'), 'maxHeatingCurrent', 1),
    (gettext('Temperature Sensor _Voltage'), gettext('V'),
        'maxSafeTemperatureSensorVoltage', 2),
    (gettext('Heating _Temperature'), gettext('°C'), 'maxSafeTemperature', 3),
    (gettext('While _Idle'), gettext('mA'), 'heatingCurrentWhileIdle', 5),
    (gettext('In _Safe Mode'), gettext('mA'), 'heatingCurrentInSafeMode', 6))


class SystemPropertiesDialogHandler(object):


    def __init__(self, system):
        self._system = system
        self._createWidgets()


    ###########################################################################
    # WIDGET CREATION                                                         #
    ###########################################################################

    def _createWidgets(self):
        """
        Creates the widget this class is responsible for.
        """
        self._createWindow()
        self._createTable()
        self._createButtons()


    def _createWindow(self):
        self._window = gtk.Window()
        self._window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
        self._window.set_title(gettext('Production System Properties'))
        self._window.connect('delete_event', self._delete)

        self._mainBox = gtk.VBox()

        self._window.add(self._mainBox)


    def _createTable(self):
        table = gtk.Table(rows=7, columns=2)
        table.set_border_width(PANEL_BORDER_WIDTH)

        thresholdsCaption = gtk.Label()
        thresholdsCaption.set_markup(gettext('<b>Safe Limits</b>'))
        table.attach(alignLeft(thresholdsCaption), 0, 2, 0, 1)

        currentsCaption = gtk.Label()
        currentsCaption.set_markup(gettext('<b>Heating Currents</b>'))
        table.attach(alignLeft(currentsCaption), 0, 2, 4, 5)

        for text, unit, name, index in DATA:
            default = getattr(self._system, name)
            entry, box = createNumberEntryWithUnit(unit, default)
            label = createMnemonicLabel(entry, text)

            setattr(self, name, default)
            setattr(self, name + 'Entry', entry)

            entry.connect('focus-out-event', self._handleParameterChange, name)
            entry.connect('key-press-event', self._handleSpecialKeys, name)

            table.attach(label, 0, 1, index, index + 1)
            table.attach(box,   1, 2, index, index + 1)

        table.set_col_spacing(0, LABEL_WIDGET_SPACING)
        table.set_row_spacing(3, PANEL_SPACING)

        tableAlignment = gtk.Alignment()
        tableAlignment.add(table)

        self._mainBox.pack_start(tableAlignment)


    def _createButtons(self):
        okButton = gtk.Button(stock=gtk.STOCK_OK)
        okButton.connect('clicked', self._handleOK)
        cancelButton = gtk.Button(stock=gtk.STOCK_CANCEL)
        cancelButton.connect('clicked', self._close)
        buttonBox = createButtonBox(okButton, cancelButton)
        self._mainBox.pack_end(buttonBox, expand=False)


    ###########################################################################
    # SIGNAL HANDLING                                                         #
    ###########################################################################

    def _handleParameterChange(self, entry, event, name):
        self._checkEntryValue(entry, name)
        return False   # The event should be propagated.


    def _checkEntryValue(self, entry, name):
        ok = True

        try:
            value = float(entry.get_text())
        except ValueError:
            fixedValue = getattr(self, name)
            ok = False
        else:
            if name in ('heatingCurrentWhileIdle', 'heatingCurrentInSafeMode'):
                minValue = 0.0
            elif name == 'maxHeatingCurrent':
                iSafe = self.heatingCurrentInSafeMode
                iIdle = self.heatingCurrentWhileIdle
                minValue = max(iSafe, iIdle, 0.1)
            else:
                minValue = 0.1

            if name in ('heatingCurrentWhileIdle', 'heatingCurrentInSafeMode'):
                maxValue = self.maxHeatingCurrent
            else:
                maxValue = None

            fixedValue = limit(value, minValue, maxValue)

            if value != fixedValue:
                ok = False

        if not ok and BEEP:
            gtk.gdk.beep()

        entry.set_text(str(float(fixedValue)))
        setattr(self, name, fixedValue)

        return ok

    # TODO: Copied from parameters.
    def _handleSpecialKeys(self, entry, event, attributeName):
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


    def _handleOK(self, *parameters):
        for text, unit, name, index in DATA:
            setattr(self._system, name, getattr(self, name))
        self._close()

    ###########################################################################

    def present(self):
        """
        Presents the dialog to the user by raising or deiconifying it.
        """
        self._window.show_all()
        self._window.present()


    def _close(self, *parameters):
        self._window.destroy()

    def _delete(self, *parameters):
        return False


