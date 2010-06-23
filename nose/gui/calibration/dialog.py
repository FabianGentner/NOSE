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
This module contains the :class:`CalibrationDialogHandler` class, which manages
a dialog that allows the user to start the calibration procedure, and to review
the data collected during previous calibration procedures. It uses widgets
implemented in :mod:`gui.listbox`, :mod:`gui.calibration.table`,
:mod:`gui.calibration.functions`, :mod:`gui.calibration.charts`,
:mod:`gui.calibration.parameters`, :mod:`gui.calibration.progress`, and
:mod:`gui.calibration.entry`.

To show the dialog, it is sufficient to create a new instance of the class and
call its :meth:`~CalibrationDialogHandler.present` method. Clients also need
to keep a reference to the handler itself to prevent it from being reclaimed
as garbage, but need not otherwise deal with it. The dialog and its components
listen for the events in the :mod:`ops.calibration.event` module to perform
their functions.

If the dialog is closed, it is just hidden, not destroyed. The client can
reuse it by calling :meth:`~CalibrationDialogHandler.present` again.
"""

# TODO: Why isn't the dialog destroyed?

import gtk

from ops.calibration.event import CalibrationStarted, CalibrationOver

import gui.listbox
import gui.calibration.table
import gui.calibration.functions
import gui.calibration.charts
import gui.calibration.parameters
import gui.calibration.progress
import gui.calibration.entry

import gui.widgets as widgets
import util

from util import gettext


#: The initial size of the calibration dialog.
DIALOG_SIZE = (750, 475)

# FIXME: Size should be adjusted for small screens.


class CalibrationDialogHandler(object):
    """
    Creates a new instance of this class, which allows the user to start the
    calibration procedure for the given :class:`ops.system.ProductionSystem`,
    and to review the data collected during its previous calibration
    procedures.
    """

    def __init__(self, system):
        self._system = system

        self._createWidgets()

        self._system.mediator.addListener(self._calibrationListener,
            CalibrationStarted, CalibrationOver)


    def _calibrationListener(self, event):
        """
        Called when a :class:`~ops.calibration.event.CalibrationStarted` or
        :class:`~ops.calibration.event.CalibrationOver` event is sent.
        Adjusts the dialog's state.
        """
        self._switchState(event.calibrationIsRunning)


    ###########################################################################
    # WIDGET CREATION                                                         #
    ###########################################################################

    def _createWidgets(self):
        """
        Creates the widget this class is responsible for.
        """
        self._createWindow()
        self._createSubordinateHandlers()
        self._createWidgetsFromName()
        self._createPanes()
        self._createButtonBar()
        self._createStatusBar()

        self._mainBox.show_all()


    def _createWindow(self):
        """
        Creates the dialog's :class:`gtk.Window` and :attr:`_mainBox`.
        """
        self._window = gtk.Window()
        self._window.set_title(gettext('Calibration'))
        self._window.set_default_size(*DIALOG_SIZE)
        self._window.connect('delete_event', util.WeakMethod(self._close))

        self._mainBox = gtk.VBox()

        self._window.add(self._mainBox)


    def _createSubordinateHandlers(self):
        """
        Creates a number subordinate handlers, which are responsible for the
        widgets the dialog can show.
        """
        self._listBoxHandler = gui.listbox.ListBoxHandler(self)

        handlerClasses = (
            #gui.calibration.table.MeasurementTableHandler,
            #gui.calibration.functions.FunctionWidgetHandler,
            gui.calibration.charts.ChartHandler,
            gui.calibration.parameters.ParameterWidgetHandler,
            gui.calibration.progress.ProgressWidgetWrapper,
            gui.calibration.entry.TemperatureEntryHandler)

        for item in handlerClasses:
            handler = item(self._system)
            name = '_' + item.__name__[0].lower() + item.__name__[1:]
            setattr(self, name, handler)


    def _createWidgetsFromName(self):
        """
        FIXME
        """
        placeholder = gtk.Label()

        self._widgetFromName = {
            'noSelection':           placeholder,
            'measurementTable':      gui.calibration.table.\
                createMeasurementTable(self._system),
            #'measurementTable':      self._measurementTableHandler.widget,
            'functionWidget':        gui.calibration.functions.\
                createFunctionWidgets(self._system),
            #'functionWidget':        self._functionWidgetHandler.widget,
            'chartParentNode':       placeholder,
            'measurementsChart':     self._chartHandler.measurementsChart,
            'temperatureChart':      self._chartHandler.temperatureChart,
            'currentChart':          self._chartHandler.currentChart,
            'calibrationParentNode': placeholder,
            'parameterWidget':       self._parameterWidgetHandler.widget,
            'progressWidget':        self._progressWidgetWrapper.widget}

        # The progress widget should initially be hidden, and should ignore
        # show_all, which is called when the user switches to it, but all its
        # children should have their show method called so that the whole
        # widget can easily be set visible.
        # TODO: Actually, the widget should be replaced with some placeholder
        #       text when no calibration is in progress.
        #pro = self._progressWidgetHandler
        #pro.widget.show_all()
        #pro.widget.hide()
        #pro.widget.set_no_show_all(True)



    def _createPanes(self):
        """
        Creates the instance of :class:`gtk.HPaned` that holds the list box and
        the switchable child widgets this dialog can show and the scrolled
        window and associated viewport that contain these widgets, and adds
        their (inital) children.
        """
        # Determine the widget that should intially be shown on the right side.
        # ListBoxHandler starts out with the first row selected.
        # TODO: Check which row is actually selected.
        path, widgetName, labelText = self._listBoxHandler.ROWS[0]
        initialWidget = self._widgetFromName[widgetName]

        self._viewport = gtk.Viewport()
        self._viewport.add(initialWidget)

        self._paned = gtk.HPaned()
        self._paned.pack1(self._listBoxHandler._widget)
        self._paned.pack2(widgets.createScrolledWindow(self._viewport))

        self._mainBox.pack_start(self._paned, expand=True)


    def _createButtonBar(self):
        """
        Creates the button bar shown at the bottom of the window.
        """
        self._closeButton = gtk.Button(stock=gtk.STOCK_CLOSE)
        self._closeButton.connect('clicked', util.WeakMethod(self._close))

        self._runCalibrationButton = widgets.createHalfStockButton(
            gtk.STOCK_EXECUTE, gettext('_Run Calibration'))
        self._runCalibrationButton.connect('clicked',
            util.WeakMethod(self._runCalibrationClicked))
        self._runCalibrationButton.show()
        self._runCalibrationButton.set_no_show_all(True)

        self._abortCalibrationButton = widgets.createHalfStockButton(
            gtk.STOCK_CANCEL, gettext('Abort Calibration'))
        self._abortCalibrationButton.connect('clicked',
            util.WeakMethod(self._abortCalibrationClicked))
        self._abortCalibrationButton.set_no_show_all(True)

        calibrationButtonBox = widgets.createButtonBox(
            self._runCalibrationButton, self._abortCalibrationButton)

        applyButton = self._temperatureEntryHandler.button

        temperatureBoxAlignment = gtk.Alignment(
            xalign=1.0, yalign=0.5, xscale=0.0)
        temperatureBoxAlignment.add(self._temperatureEntryHandler.box)

        buttonBarBox = gtk.HBox()
        buttonBarBox.pack_start(calibrationButtonBox, expand=False)
        buttonBarBox.pack_start(temperatureBoxAlignment, expand=True)
        buttonBarBox.pack_end(widgets.createButtonBox(
            applyButton, self._closeButton), expand=False)


        self._mainBox.pack_start(buttonBarBox, expand=False)


    def _createStatusBar(self):
        """
        Creates the status bar shown at the very bottom of the window.
        """
        pro = self._progressWidgetWrapper.handler

        self._progressBar = gtk.ProgressBar()
        self._progressBar.set_no_show_all(True)

        self._statusLabel = gtk.Label()
        self._statusLabel.set_alignment(0.0, 0.5)

        textNoWait = gettext('%(action)s')
        text = textNoWait + gettext(': %(stageTimeLeft)s remaining')

        pro.addStageProgressBar(self._progressBar, showText=False)
        pro.addProgressLabel(self._statusLabel, text, textNoWait)

        self._statusBar = gtk.HBox()
        self._statusBar.set_spacing(widgets.PANEL_BORDER_WIDTH)
        self._statusBar.pack_start(self._statusLabel)
        self._statusBar.pack_start(self._progressBar, expand=False)

        self._mainBox.pack_start(gtk.HSeparator(), expand=False)
        self._mainBox.pack_start(self._statusBar, expand=False)


    ###########################################################################
    # WIDGET SIZE FIXES                                                       #
    ###########################################################################

    def _fixWidgetSizes(self):
        """
        Makes some tweaks to the size of several widgets in order to avoid ugly
        jumps in the layout when these widgets' visibilities change.

        The dialog must be visible when this method is called.
        """
        self._fixButtonSizes()
        self._fixStatusBarHeight()


    def _fixButtonSizes(self):
        """
        Makes sure the Run Calibration button and the Abort Calibration button
        have the same size. This is important, since one takes the place of the
        other depending on whether a calibration procedure is in progress, so
        having them at unequal sizes would lead to ugly layout jumps. Also
        makes sure the buttons are as high as the Close button.

        The dialog must be visible when this method is called.
        """
        runVisible = self._runCalibrationButton.get_property('visible')
        abortVisible = self._abortCalibrationButton.get_property('visible')

        assert runVisible ^ abortVisible
        assert abortVisible is self._system.isBeingCalibrated

        self._runCalibrationButton.set_property('visible', True)
        self._abortCalibrationButton.set_property('visible', True)

        cbx, cby, cbw, cbh = self._closeButton.get_allocation()
        rbx, rby, rbw, rbh = self._runCalibrationButton.get_allocation()
        abx, aby, abw, abh = self._abortCalibrationButton.get_allocation()

        w = max(cbw, rbw, abw)
        h = max(cbh, rbh, abh)

        self._closeButton.set_size_request(-1, h)   # Use natural width.
        self._runCalibrationButton.set_size_request(w, h)
        self._abortCalibrationButton.set_size_request(w, h)

        self._runCalibrationButton.set_property('visible', runVisible)
        self._abortCalibrationButton.set_property('visible', abortVisible)

        # This method doesn't have good unit tests. Check changes manually!


    def _fixStatusBarHeight(self):
        """
        Makes sure the progress label and the progress bar have the same
        height. This is important, since the latter is hidden when no
        calibration procedure is in progress, so it being higher than the
        label would lead to ugly jumps in the height of the status bar.

        The dialog must be visible when this method is called.
        """
        assert self._statusLabel.get_property('visible')
        x, y, w, h = self._statusLabel.get_allocation()
        self._statusBar.set_size_request(-1, h)   # Use natural width.

        # This method doesn't have good unit tests. Check changes manually!


    ###########################################################################
    # CALLBACKS                                                               #
    ###########################################################################

    def _runCalibrationClicked(self, button):
        """
        Called when the user clicks the Run Calibration button. Starts the
        calibration procedure.
        """
        currents = self._parameterWidgetHandler.getCurrents()
        self._system.startCalibration(currents)


    def _abortCalibrationClicked(self, button):
        """
        Called when the user clicks the Abort Calibration button.
        """
        self._confirmAbort()


    ###########################################################################
    # FUNCTIONALITY                                                           #
    ###########################################################################

    def present(self):
        """
        Presents the dialog to the user by raising or deiconifying it.
        """
        self._window.present()
        self._fixWidgetSizes()


    def _switchWidget(self, newWidgetName):
        """
        Switches the child widget displayed in the dialog to the named one.
        """
        self._viewport.remove(self._viewport.get_child())
        self._viewport.add(self._widgetFromName[newWidgetName])
        self._viewport.show_all()


    def _switchState(self, calibrationInProgress):
        """
        Changes the visibility and sensitivity of the widget that make up the
        dialog to the appropriate state when a calibration procedure is started
        or finished.
        """
        cip = calibrationInProgress

        self._abortCalibrationButton.set_property('visible', cip)
        self._runCalibrationButton.set_property('visible', not cip)
        self._parameterWidgetHandler.widget.set_sensitive(not cip)
        #TODO
        #self._progressWidgetHandler.widget.set_property('visible', cip)
        self._progressBar.set_property('visible', cip)

        if not cip:
            self._statusLabel.set_text('')


    def _confirmAbort(self):
        """
        Shows a dialog that asks the user to confirm the abortion of the
        calibration procedure, and aborts it if the reply is affirmative.
        """
        answer = widgets.askUser(self._window, gettext(
            'Are you sure you want to abort the calibration procedure?'))
        if answer:
            self._system.abortCalibration()
        return answer


    def _close(self, *parameters):
        """
        A signal handler that hides the dialog. Called when it receives a
        delete event, or when the close button is clicked. The dialog can
        be reused by calling :meth:`present` again.
        """
        if not self._system.isBeingCalibrated or self._confirmAbort():
            self._window.hide()

        return True   # Prevents the destruction of the window and its widgets.

