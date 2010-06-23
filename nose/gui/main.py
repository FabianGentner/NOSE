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

import pygtk
import gobject
import gtk
import os.path
import weakref

from gui.calibration.dialog import CalibrationDialogHandler
from gui.systemprops import SystemPropertiesDialogHandler

import gui.actions
import util


###############################################################################
# ASSORTED PARAMETERS                                                         #
###############################################################################

# The name of the program.
PROGRAM_NAME = 'NOSE'


# The path to the XML file that contains the layout of the main window's menu.
MENU_DEFINITION_PATH = os.path.join('nose', 'gui', 'menu.xml')

# The path to the file containing the application's icon.
ICON_PATH = os.path.join('resources', 'icon.png')


# The default size of the main window. Its actual width and height will not
# exceed the screens width and height times MAIN_WINDOW_MAX_SCREEN_FRACTION,
# respectively.
MAIN_WINDOW_SIZE = (800, 600)

# The maximum fraction of the screen's height and width the main window is
# allowed to occupy.
MAIN_WINDOW_MAX_SCREEN_FRACTION = 0.8


# The time between updates of the main window's status bar, in milliseconds.
STATUS_BAR_UPDATE_INTERVAL = 250



###############################################################################
# SETUP                                                                       #
###############################################################################

gtk.gdk.threads_init()
gtk.window_set_default_icon_from_file(ICON_PATH)


###############################################################################
# MAIN WINDOW HANDLER                                                         #
###############################################################################

# A list of all MainWindowHandlers whose start method has been called, but
# whose destroy method has not yet been called. Used in case the progream
# allows multiple main windows to coexist in the future. Also, makes sure
# that there's always a reference to these handlers around so that they
# don't get inadvertently garbage-collected if a client doesn't keep a
# reference itself.
MAIN_WINDOW_HANDLERS = []



class MainWindowHandler(object):
    """
    A class that handles the creation of the application's main window and
    implements its functionality. There can be any number of main windows,
    which are each responsible for a different system, although the
    program currently uses only a single main window.
    """

    # The actual gtk.Window.
    _window = None

    # The gtk.VBox that serves as the top-level container of the widgets that
    # make up the main window.
    _mainBox = None

    # A gtk.Label on the status bar that shows the current heating temperature.
    _temperatureLabel = None


    # The system the user can interact with using the main window.
    # TODO: This cannot currently be safely changed.
    _system = None


    # The gui.calibration.dialog.CalibrationDialogHandler associated with this
    # main window. This remains set even if the dialog is closed. Saved here to
    # prevent multiple copies of the dialog from being shown, and to prevent it
    # from being collected prematurely.
    _calibrationDialogHandler = None

    # A list of gui.action.NoseAction objects for the actions that can be
    # activated from the main window's menu bar. Saved here to prevent them
    # from being collected prematurely.
    _actions = None



    def __init__(self, mediator, system):
        """
        Creates a handler for a main window that allows the user to interact
        with the given system.
        """
        # TOOD: What is the mediator used for? Why both mediator and system?
        self.mediator = mediator
        self._system = system
        self._actions = []
        self._createWidgets()

        self._systemPropertiesDialogHandler = lambda: None


    def start(self):
        """
        Shows the gtk.Window and starts GTK's main loop if this is the first
        MainWindowHandler whose start method has been called.
        """
        self._window.show_all()
        MAIN_WINDOW_HANDLERS.append(self)
        if len(MAIN_WINDOW_HANDLERS) == 1:
            gtk.main()


    def destroy(self, window=None, options=None):
        """
        Destroys the gtk.Window and quits GTK's main loop if this is the last
        MainWindowHandler whise destroy method has not yet been called.
        """
        self._window.destroy()
        MAIN_WINDOW_HANDLERS.remove(self)
        if len(MAIN_WINDOW_HANDLERS) == 0:
            gtk.main_quit()


    ###########################################################################
    # WINDOW CREATION                                                         #
    ###########################################################################

    def _createWidgets(self):
        """
        Creates the window and its contents.
        """
        self._createWindow()
        self._createMenu()
        self._createStatusBar()


    def _createWindow(self):
        """
        Creates the gtk.Window object itself, but not its nontrivial contents.
        """
        self._window = gtk.Window()
        self._window.set_title(PROGRAM_NAME)
        self._window.set_default_size(*self._getPreferredSize())
        self._window.connect('destroy', util.WeakMethod(self.destroy))
        self._mainBox = gtk.VBox(homogeneous=False)
        self._window.add(self._mainBox)


    def _createMenu(self):
        """
        Creates the window's menu. Its layout can be found in menu.xml, and
        implementation of the actions taken when a menu item is activated as
        well as i18n is in the actions package.
        """
        actionGroup = gui.actions.createActionGroup(self)

        uiManager = gtk.UIManager()
        uiManager.insert_action_group(actionGroup, 0)
        uiManager.add_ui_from_file(MENU_DEFINITION_PATH)

        self._window.add_accel_group(uiManager.get_accel_group())
        self._mainBox.pack_start(
            uiManager.get_widget('/MenuBar'), expand=False)



    def _createStatusBar(self):
        """
        Creates the status bar at the bottom of the window.
        """
        self._temperatureLabel = gtk.Label()
        self._mainBox.pack_end(self._temperatureLabel, expand=False)
        self._mainBox.pack_end(gtk.HSeparator(), expand=False)

        gobject.timeout_add(STATUS_BAR_UPDATE_INTERVAL,
            util.WeakMethod(self._updateStatusBar))


    ###########################################################################
    # SUBORDINATE DIALOGS                                                     #
    ###########################################################################

    def showCalibrationDialog(self):
        """
        Shows the calibration dialog. The first time this method is called,
        the dialog is created
        """
        if self._calibrationDialogHandler == None:
            self._calibrationDialogHandler = CalibrationDialogHandler(
                self._system)

        self._calibrationDialogHandler.present()


    def showSystemPropertiesDialog(self):
        dialog = self._systemPropertiesDialogHandler()
        if dialog == None:
            dialog = SystemPropertiesDialogHandler(self._system)
            self._systemPropertiesDialogHandler = weakref.ref(dialog)

        dialog.present()


    ###########################################################################
    # UPDATES                                                                 #
    ###########################################################################

    def _updateStatusBar(self):
        """
        Updates the information shown in the window's status bar. This method
        is called by GTK in the main event loop.
        """
        temperature = self._system.temperature
        voltage = self._system.temperatureSensorVoltage
        if temperature != None:
            text = u'%d °C' % temperature
        else:
            text = u'%s V' % util.stringFromFloat(voltage, 4, False)
        self._temperatureLabel.set_text(text)

        # TODO: The timeout is never properly removed.
        return True   # Yes, this method should be called again.


    ###########################################################################
    # UTILITY METHODS                                                         #
    ###########################################################################

    def _getPreferredSize(self, screen=None):
        """
        Figures out an appropriate size for the main window. Its size is set
        to MAIN_WINDOW_SIZE, unless this would cause the window's width or
        height to exceed a fraction of the available width or height that
        exceeds MAIN_WINDOW_MAX_SCREEN_FRACTION.

        The parameter screen is the gtk.gdk.Screen the window needs to fit on.
        If it is None, the window's current screen is used, which should be the
        desired behavior in all cases; the parameter is chiefly provided for
        testing purposes.

        This method jumps through some hoops to properly handle the corner
        case of a virtual screens that is made up of multiple small monitors.
        """
        MSF = MAIN_WINDOW_MAX_SCREEN_FRACTION
        width, height = MAIN_WINDOW_SIZE
        screen = screen or self._window.get_screen()
        if screen:
            # Find the smallest width and height among the monitors that
            # make up the screen.
            for n in range(screen.get_n_monitors()):
                geometry = screen.get_monitor_geometry(n)
                width = min(width, int(MSF * geometry.width))
                height = min(height, int(MSF * geometry.height))
        return width, height

