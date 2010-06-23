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
This module contains the :class:`MeasurementTableHandler` class, which manages
a table that shows the measurements collected during the :term:`calibration
procedure`. The handler also allows the user to delete selected measurements
and to start a new calibration procedure to retake selected measurements.

Clients need not actually deal with the :class:`MeasurementTableHandler`
itself; instead, they can use the :func:`createMeasurementTable` function,
which creates the handler and returns the widget used for the table (a
:class:`gtk.TreeView`). The table will be automatically updated when the
calibration data of the :class:`~ops.system.ProductionSystem` passed to
the function changes.

|

.. image:: table.png
    :align: center

|
"""

import gtk

from gui.widgets import createCellDataRounder, addMenuItem
from ops.calibration.event import CalibrationDataChanged
from util import gettext, ngettext


def createMeasurementTable(system):
    """
    Creates a :class:`MeasurementTableHandler` and returns the widget it uses
    for the table. `system` is the :class:`~ops.system.ProductionSystem` whose
    calibration measurements are to be shown.
    """
    return MeasurementTableHandler(system).widget


###############################################################################
# CONSTANTS                                                                   #
###############################################################################

#: A tuple that lists the localized titles for the columns that show the
#: heating current, temperature sensor voltage, and heating temperature.
COLUMN_TITLES = (
    gettext('Current [mA]'),
    gettext('Voltage [V]'),
    gettext('Temperature [°C]'))

#: A tuple that lists the maximum number of fractional digits that are to
#: be used for heating currents, temperature sensor voltages, and heating
#: temperatures.
FRACTIONAL_DIGITS = (8, 3, 0)
# Up to eight digits are shown for the current, because it has usually been
# entered by the user, and suppressing digits the user knows should be there
# violates the principle of least surprise. Also, the number of digits should
# be limited by the ParameterWidgetHandler in any case, so the limit should
# never actually matter.

#: A tuple that lists whether trailing zeros of the fractional part of the
#: heating currents, temperature sensor voltages, and heating temperatures
#: (and the dot, if there is no fractional part) should be omitted.
TRIM_TRAILING_ZEROS = (True, False, True)


###############################################################################
# MEASUREMENT TABLE HANDLER                                                   #
###############################################################################

class MeasurementTableHandler(object):
    """
    Creates a new instance of this class that shows the measurements collected
    during the calibration of the given :class:`~ops.system.ProductionSystem`.
    """

    def __init__(self, system):
        self._system = system
        system.mediator.addListener(self._handleUpdate, CalibrationDataChanged)
        self._createWidgets()
        self._updateTable(system.calibrationData)


    @property
    def widget(self):
        """The :class:`gtk.TreeView` used for the table. Immutable."""
        return self._treeView


    ###########################################################################
    # WIDGET CREATION                                                         #
    ###########################################################################

    def _createWidgets(self):
        """
        Creates the widgets this class is responsible for.
        """
        self._listStore = gtk.ListStore(float, float, float)

        self._treeView = gtk.TreeView(self._listStore)
        self._treeView.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        self._treeView.connect('button-press-event', self._buttonPressed)

        renderer = gtk.CellRendererText()
        renderer.set_property('xalign', 0.5)   # Alignment of the contents.

        for index in xrange(3):
            rounder = createCellDataRounder(
                index, FRACTIONAL_DIGITS[index], TRIM_TRAILING_ZEROS[index])

            column = gtk.TreeViewColumn(COLUMN_TITLES[index], renderer)
            column.set_cell_data_func(renderer, rounder)
            column.set_alignment(0.5)   # Alignment of the title.
            column.set_expand(True)

            self._treeView.append_column(column)


    ###########################################################################
    # UPDATE HANDLING                                                         #
    ###########################################################################

    def _handleUpdate(self, event):
        """
        Called when a :class:`~ops.calibration.event.CalibrationDataChanged`
        event is sent. Updates the table.
        """
        self._updateTable(event.calibrationData)


    def _updateTable(self, calibrationData):
        """
        Updates the information shown in the table to reflect changes in the
        calibration data.
        """
        self._listStore.clear()
        for m in calibrationData.measurements:
            self._listStore.append(m)


    ###########################################################################
    # POP-UP MENU                                                             #
    ###########################################################################

    def _buttonPressed(self, widget, event):
        """
        Called when the user presses a mouse button on the table. If it is the
        right mouse button, a pop-up menu is shown that allows the user to
        retake or delete the selected measurements.
        """
        if event.button == 3:
            self._showPopupMenu(event)
            return True    # The event should not be propagated.
        else:
            return False   # The event should be propagated.


    def _showPopupMenu(self, event):
        """
        Shows the popup menu that allows the user to retake or delete the
        selected measurements.
        """
        UNUSED, rows = self._treeView.get_selection().get_selected_rows()
        currents = self._currentsFromRows(rows)

        retakeText = ngettext(
            '_Retake Selected Measurement',
            '_Retake Selected Measurements', len(currents))
        deleteText = ngettext(
            '_Delete Selected Measurement',
            '_Delete Selected Measurements', len(currents))

        menu = gtk.Menu()
        retakeItem = addMenuItem(menu, retakeText, gtk.STOCK_REFRESH,
            self._retakeSelectedMeasurementsActivated, currents)
        deleteItem = addMenuItem(menu, deleteText, gtk.STOCK_DELETE,
            self._deleteSelectedMeasurementsActivated, currents)
        menu.show_all()

        if len(currents) == 0 or self._system.isLocked:
            retakeItem.set_sensitive(False)
            deleteItem.set_sensitive(False)

        # The first three parameters are only relevant for submenus.
        menu.popup(None, None, None, event.button, event.time)

        return menu   # For testing purposes.


    def _retakeSelectedMeasurementsActivated(self, widget, currents):
        """
        Called when the user activates :guilabel:`Retake Selected Measurements`
        from the table's pop-up menu. Starts a calibration procedure to take
        new measurements for the given currents.
        """
        self._system.startCalibration(currents)


    def _deleteSelectedMeasurementsActivated(self, widget, currents):
        """
        Called when the user activates :guilabel:'Delete Selected Measurements'
        from the table's pop-up menu. Deletes the measurements for the given
        currents from the system's calibration data.
        """
        for i in currents:
            self._system.calibrationData.removeMeasurement(i)


    def _currentsFromRows(self, rows):
        """
        Returns a tuple of the heating currents shown in the given rows of the
        table, as floats.
        """
        return tuple(self._listStore[row][0] for row in rows)

