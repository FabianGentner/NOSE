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
Creates a series of :class:`gtk.Action` objects that encapsulate the operations
the user can start from the main window's menu. (For the actions in the Debug
menu, see :mod:`gui.debug`.)

Clients normally only need to call :func:`createActionGroup` to receive a
:class:`gtk.ActionGroup` consisting of all the actions.

To create a new action, you need to:

* subclass :class:`NoseAction` and set the subclass's :attr:`NoseAction.name`
  and :attr:`NoseAction.text` attributes, optionally set some of the other
  attributes, and override the :meth:`gui.actions.NoseAction.run` method;
* add the action to the action group created in :func:`createActionGroup`; and
* add an entry to :file:`gui/resources/menu.xml`.
"""

import gtk

from ops.calibration.event import CalibrationDataChanged

import gui.io
import gui.widgets as widgets
import ops.calibration.data
import util

from util import gettext


#: An error message that is displayed if the user activates an action when the
#: system isn't calibrated even though that is not supposed to be possible
#: for that action. Should only be needed if something goes very, very wrong.
NOT_CALIBRATED_ERROR_MESSAGE = gettext(
    'This function is only available when the system is calibrated.')
    # TODO: Not currently used.

#: An error message that is displayed if the user activates an action when the
#: system's calibration data has no measurements even though that is not
#: supposed to be possible for that action. Should only be needed if something
#: goes very, very wrong.
NO_CALIBRATION_DATA_ERROR_MESSAGE = gettext(
    'This function is only available when the system has calibration data.')

#: An error message that is displayed if the user activates an action when the
#: system isn't simulated even though that is not supposed to be possible for
#: that action. Should only be needed if something goes very, very wrong.
NO_SIMULATION_ERROR_MESSAGE = gettext(
    'This function is only available for simulated devices.')


###############################################################################
# NOSE ACTION                                                                 #
###############################################################################

class NoseAction(object):
    """
    An abstract base class for actions the user can perform in *NOSE*.
    Simplifies the creation of :class:`gtk.Action` and :class:`gtk.RadioAction`
    instances, and keeps a :class:`gui.main.MainWindowHandler` around that
    might be required by many actual actions.


    **Instance Attributes**

    mainWindowHandler:
        The :class:`gui.main.MainWindowHandler` this action is associated with.

    system:
        A property that provides convenient access to the
        :attr:`mainWindowHandler`'s system.

    gtkAction:
        The :class:`gtk.Action` or :class:`gtk.RadioAcition` associated with
        this :class:`NoseAction`.
    """

    #: The action's unique internal name, as used in :file:`menu.xml`.
    name = None

    #: The text shown in menu items associated with the action. Underscores can
    #: be used to create shortcuts.
    text = None

    #: An optional stock ID (:data:`gtk.STOCK_FOO`) that is used by the action.
    #: Determines the icon (except for radio actions) and maybe the
    #: accelerator.
    stock = None

    #: An optional accelerator, such as ``'<Ctrl><Alt>X'``. When in doubt,
    #: check :func:`gtk.accelerator_parse`. Should be internationalized.
    accelerator = None

    #: If set, the action becomes a radio action, that is, it can be toggled
    #: between an active and an inactive state, and only one action with the
    #: given :attr:`radioGroupName` can be active at any time.
    radioGroupName = None

    #: An arbitrary integer that is used as the value for radio actions. See
    #: :class:`gtk.RadioAction`. Can be safely ignored.
    radioValue = 0

    #: Determines whether a radio action should be set to be initially active.
    #: Should only be set to ``True`` for one action in a given action group.
    radioActive = False


    #: If set to ``True``, the action can only be activated if the system
    #: has at least one calibration measurement. If it isn't, the action is
    #: automatically set insensitive.
    requiresCalibrationData = False

    #: If set to ``True``, the action an only be activated if the system
    #: is simulated.
    requiresSimulation = False


    # Provides convenient access to the mainWindowHandler's system.
    system = property(lambda self: self.mainWindowHandler._system)


    def __init__(self, mainWindowHandler, actionGroup):
        """
        Creates a new instance of this class that is associated with
        the given :class:`gui.main.MainWindowHandler`, and creates a
        :class:`gtk.Action` or :class:`gtk.RadioAction` that belongs
        to the given :class:`gtk.ActionGroup`.
        """
        self.mainWindowHandler = mainWindowHandler

        parameters = [self.name, self.text, None, self.stock]

        if self.radioGroupName:
            self.gtkAction = gtk.RadioAction(*(parameters + [self.radioValue]))
        else:
            self.gtkAction = gtk.Action(*parameters)

        self.gtkAction.connect('activate', util.WeakMethod(self.activate))

        if self.radioGroupName:
            # Find another action in the same action group and join its group.
            # This needs to be done *before* the action is added to
            # mainWindowHandler._actions.
            for other in mainWindowHandler._actions:
                if other.radioGroupName == self.radioGroupName:
                    self.gtkAction.set_group(other.gtkAction)
                    break
            if self.radioActive:
                self.gtkAction.activate()

        if self.requiresSimulation:
            # TODO: Assumes the MainWindowHandler's system never changes.
            if not self.system.isSimulation:
                self.gtkAction.set_sensitive(False)

        if self.requiresCalibrationData:
            # TODO: This should be added to the MainWindowHandler,
            # not the system.
            self.system.mediator.addListener(
                self._handleCalibrationDataChange, CalibrationDataChanged)
            # TODO: Duplicate code.
            self.gtkAction.set_sensitive(
                self.system.calibrationData.hasMeasurements)

        actionGroup.add_action_with_accel(self.gtkAction, self.accelerator)
        mainWindowHandler._actions.append(self)


    def activate(self, *parameters):
        """
        Called when the action is activated. Calls :meth:`run`, unless its not
        supposed to be possible to activate the action right now.
        """
        error = None

        # None of these cases should actually be possible, but we properly
        # handle illegal activations nonetheless.
        if self.requiresCalibrationData:
            if not self.system.calibrationData.hasMeasurements:
                error = NO_CALIBRATION_DATA_ERROR_MESSAGE
        elif self.requiresSimulation and not self.system.isSimulation:
            error = NO_SIMULATION_ERROR_MESSAGE

        if error:
            widgets.reportError(self.mainWindowHandler._window,
                error, None, 'illegal activation')
        else:
            self.run()


    def run(self):
        """
        Called when the action is activated. Subclasses need to be override
        this method.
        """
        assert False, 'abstract method called'


    def _handleCalibrationDataChange(self, event):
        """
        Receives calibration data change events if :attr:`requiresCalibration`
        is set to ``True``, and sets the action's sensitivity depending on
        whether the system is calibrated.
        """
        if self.requiresCalibrationData:
            self.gtkAction.set_sensitive(event.calibrationData.hasMeasurements)


###############################################################################
# FILE MENU ACTIONS                                                           #
###############################################################################

class QuitAction(NoseAction):
    """Quits the program."""
    name = 'quit'
    text = gettext('_Quit')
    stock = gtk.STOCK_QUIT

    def run(self):
        self.mainWindowHandler.destroy()


###############################################################################
# SYSTEM MENU ACTIONS                                                         #
###############################################################################

class EditSystemProperiesAction(NoseAction):
    """Allows the user to edit the properties of the production system."""
    name = 'editSystemProperties'
    text = gettext('Edit System _Properties...')
    stock = gtk.STOCK_EDIT

    def run(self):
        self.mainWindowHandler.showSystemPropertiesDialog()


###############################################################################
# CALIBRATION MENU ACTIONS                                                    #
###############################################################################

class ShowCalibrationDialogAction(NoseAction):
    """Shows the calibration dialog."""
    name = 'showCalibrationDialog'
    text = gettext('Show _Calibration Dialog...')
    stock = gtk.STOCK_INFO
    accelerator = gettext('<Shift><Ctrl>C')

    def run(self):
        self.mainWindowHandler.showCalibrationDialog()


class LoadCalibrationDataAction(NoseAction):
    """Loads the calibration data from a file."""
    name = 'loadCalibrationData'
    text = gettext('_Load Calibration Data...')
    stock = gtk.STOCK_OPEN

    def run(self):
        parent = self.mainWindowHandler._window
        cd = gui.io.load('CalibrationData', None, parent)
        if cd is None:
            pass   # If there was an error, it has already been reported.
        else:
            self.system.calibrationData = cd


class SaveCalibrationDataAction(NoseAction):
    """Saves the calibration data to a file."""
    name = 'saveCalibrationData'
    text = gettext('_Save Calibration Data')
    stock = gtk.STOCK_SAVE
    requiresCalibrationData = True

    def run(self):
        parent = self.mainWindowHandler._window
        cd = self.system.calibrationData
        gui.io.save(cd, 'CalibrationData', cd.fileName, parent)


class SaveCalibrationDataAsAction(NoseAction):
    """Saves the calibration data to a new file."""
    name = 'saveCalibrationDataAs'
    text = gettext('Save Calibration Data _As...')
    stock = gtk.STOCK_SAVE_AS
    requiresCalibrationData = True

    def run(self):
        parent = self.mainWindowHandler._window
        cd = self.system.calibrationData
        gui.io.save(cd, 'CalibrationData', None, parent)


class ClearCalibrationDataAction(NoseAction):
    """Clears the calibration data."""
    name = 'clearCalibrationData'
    text = gettext('Clear Calibration Data')
    stock = gtk.STOCK_CLEAR
    requiresCalibrationData = True

    def run(self):
        parent = self.mainWindowHandler._window
        message = gettext('Really clear the calibration data?')
        if widgets.askUser(parent, message):
            # TODO: Should not create a new object!
            #       Actually, should create a new object!
            newCD = ops.calibration.data.CalibrationData()
            self.system.calibrationData = newCD


###############################################################################
# CREATE ACTIONS                                                              #
###############################################################################

def createActionGroup(mainWindowHandler):
    """
    Creates a :class:`gtk.ActionGroup` object with the actions that are
    required to create the main window's menu. The actions that are created
    are added to ``mainWindowHandler._actions``.
    """
    actionGroup = gtk.ActionGroup('actions')

    # FILE MENU
    _makeMenuAction('file', gettext('_File'), actionGroup)
    QuitAction(mainWindowHandler, actionGroup)

    # SYSTEM MENU
    _makeMenuAction('system', gettext('_System'), actionGroup)
    EditSystemProperiesAction(mainWindowHandler, actionGroup)

    # CALIBRATION MENU
    _makeMenuAction('calibrate', gettext('_Calibrate'), actionGroup)
    ShowCalibrationDialogAction(mainWindowHandler, actionGroup)
    LoadCalibrationDataAction(mainWindowHandler, actionGroup)
    SaveCalibrationDataAction(mainWindowHandler, actionGroup)
    SaveCalibrationDataAsAction(mainWindowHandler, actionGroup)
    ClearCalibrationDataAction(mainWindowHandler, actionGroup)

    import gui.debug
    gui.debug.createDebugActions(mainWindowHandler, actionGroup)

    return actionGroup



def _makeMenuAction(name, text, actionGroup):
    """
    For some reason, GTK wants actions associated with menu items that
    have a submenu. This function creates them.
    """
    actionGroup.add_action(gtk.Action(name, text, None, None))


