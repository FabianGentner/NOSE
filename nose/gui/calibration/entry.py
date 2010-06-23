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
This module contains the :class:`TemperatureEntryHandler` class, which
manages a number of widgets that allow the user to enter :term:`temperature
measurements <temperature measurement>` when they are requested during the
:term:`calibration procedure`.

These widgets are

* a :class:`gtk.HBox` (:attr:`~TemperatureEntryHandler.box`) that contains the
  :class:`gtk.Entry` used to enter temperature measurements, a label that
  indicates that the measurement is in °C, and optionally a label that
  identifies the entry; and

* a :class:`gtk.Button` (:attr:`~TemperatureEntryHandler.button`) that can be
  pressed to finalize the temperature input.

Since the ideal positioning of these widgets greatly depends on the context in
which they are used, the :class:`TemperatureEntryHandler` does not provide a
container that contains both widgets. Instead, the client needs to add them
separately to the GUI.

Clients also need to keep a reference to the handler itself to prevent it from
being reclaimed as garbage.

The handler listens to :class:`~ops.calibration.event.TemperatureRequested`
and :class:`~ops.calibration.event.TemperatureRequestOver` events to ensure
that the widgets in the :attr:`~TemperatureEntryHandler.box` are only
sensitive while there is an unanswered temperature request, and that the
:attr:`~TemperatureEntryHandler.button` is only sensitive while there is an
unanswered temperature request and the entered temperature measurement is an
integer.

Using several :class:`TemperatureEntryHandler` instances simultaneously is
possible.
"""

import gtk
import re

from ops.calibration.event import *

import gui.widgets as widgets
import util

from util import gettext


###############################################################################
# TEMPERATURE ENTRY HANDLER                                                   #
###############################################################################

class TemperatureEntryHandler(object):
    """
    Creates a new instance of this class, which accepts temperature
    measurements for the given :class:`~ops.system.ProductionSystem`.

    `buttonStock` is the GTK stock item used for the :attr:`button` (the
    default is :attr:`gtk.STOCK_APPLY`, but clients may want to use
    :attr:`gtk.STOCK_OK` instead); `useLabel` determines whether :attr:`box`
    contains a label that identifies the :class:`gtk.Entry`.
    """

    def __init__(self, system, buttonStock=gtk.STOCK_APPLY, useLabel=True):
        self._callback = None
        system.mediator.addListener(self._temperatureRequestListener,
            TemperatureRequested, TemperatureRequestOver)
        self._createWidgets(buttonStock, useLabel)


    @property
    def box(self):
        """
        A :class:`gtk.HBox` that contains the :class:`gtk.Entry` used to enter
        temperature measurements, a label that indicates that the measurement
        is in °C, and optionally a label that identifies the entry. Immutable.
        """
        return self._box


    @property
    def button(self):
        """
        A :class:`gtk.Button` that can be pressed to finalize the temperature
        input. Immutable.
        """
        return self._button


    def _temperatureRequestListener(self, event):
        """
        Called when a :class:`~ops.calibration.event.TemperatureRequested` or
        :class:~`ops.calibration.event.TemperatureRequestOver` event is sent.
        Sets the widgets sensitive or insensitive, and sets or clears
        :attr:`_callback`.
        """
        if event.temperatureRequested:
            self._callback = event.callback
            self.box.set_sensitive(True)
            self._entry.set_text('')
            self._entry.grab_focus()
        else:
            self._callback = None
            self.box.set_sensitive(False)
            self.button.set_sensitive(False)


    ###########################################################################
    # WIDGET CREATION                                                         #
    ###########################################################################

    def _createWidgets(self, buttonStock, useLabel):
        """
        Creates the widgets this class is responsible for.
        """
        unit = gettext('°C')
        self._entry, unitBox = widgets.createNumberEntryWithUnit(unit)
        self._entry.connect('changed', util.WeakMethod(self._textChanged))

        if useLabel:
            label = gtk.Label(gettext('_Temperature Measurement'))
            label.set_alignment(1.0, 0.5)
            label.set_use_underline(True)
            label.set_mnemonic_widget(self._entry)

            self._box = gtk.HBox()
            self._box.set_spacing(widgets.SPACING['wide'])
            self._box.pack_start(label)
            self._box.pack_start(unitBox)
        else:
            self._box = unitBox

        self._box.set_sensitive(False)

        self._button = gtk.Button(stock=buttonStock)
        self._button.set_sensitive(False)
        self._button.connect('clicked', util.WeakMethod(self._buttonClicked))

        hierarchyChanged = util.WeakMethod(self._hierarchyChanged)
        self._box.connect('hierarchy-changed', hierarchyChanged)
        self._button.connect('hierarchy-changed', hierarchyChanged)


    ###########################################################################
    # SIGNAL HANDLING                                                         #
    ###########################################################################

    def _hierarchyChanged(self, widget, oldToplevel):
        """
        Called when the :attr:`box` or the :attr:`button` or one of their
        ancestors changes their parents. Sets the button as the entry's
        default widget if both are still in the containment hierarchy.
        This is necessary because the default cannot be set until the widgets
        are in a window.
        """
        if widgets.isInWindow(self.box) and widgets.isInWindow(self.button):
            widgets.arrangeDefaulting(self.button, self._entry)


    def _textChanged(self, entry):
        """
        Called when the text in :attr:`_entry` changes. Ensures that the
        button is enabled if and only if the text is a positive integer.
        """
        isInteger = (re.match('^\d+$', self._entry.get_text()) != None)
        self.button.set_sensitive(isInteger)


    def _buttonClicked(self, button):
        """
        Called when the button is clicked. Calls the callback function.
        """
        # The entry must contain a valid integer at this point.
        temperature = int(self._entry.get_text())
        self._callback(temperature)

