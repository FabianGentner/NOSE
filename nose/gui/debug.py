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

import gc
import gobject
import gtk

from gui.actions import NoseAction, _makeMenuAction
from util import gettext


def createDebugActions(mainWindowHandler, actionGroup):
    _makeMenuAction('debug', gettext('_Debug'), actionGroup)
    MagicCalibrationAction(mainWindowHandler, actionGroup)
    FakeCalibrationAction(mainWindowHandler, actionGroup)
    ShowMagicPyrometerAction(mainWindowHandler, actionGroup)
    SetCalibrationSpeedNormalAction(mainWindowHandler, actionGroup)
    SetCalibrationSpeed5Action(mainWindowHandler, actionGroup)
    SetCalibrationSpeed10Action(mainWindowHandler, actionGroup)
    SetCalibrationSpeed25Action(mainWindowHandler, actionGroup)
    CollectGarbageAction(mainWindowHandler, actionGroup)



###############################################################################
# DEBUG MENU ACTIONS                                                          #
###############################################################################

class MagicCalibrationAction(NoseAction):
    """Calibrates the system using data from the simulation object."""
    name = 'magicCalibration'
    text = gettext('Perform Magic _Calibration')
    stock = gtk.STOCK_EXECUTE
    requiresSimulation = True

    def run(self):
        self.system.performMagicCalibration()


class FakeCalibrationAction(NoseAction):
    name = 'fakeCalibration'
    text = gettext('Use a _Fake Calibration Procedure')
    requiresSimulation = True

    def run(self):
        self.system.testingUseFakeCalibration = True


class ShowMagicPyrometerAction(NoseAction):
    """
    Shows a pytometer that receives temperatures from the simulation object.
    """
    name = 'showMagicPyrometer'
    text = gettext('Show Magic _Pyrometer')
    stock = gtk.STOCK_INFO
    requiresSimulation = True

    def run(self):
        MagicPyrometer(self.system).show()


class SetCalibrationSpeedAction(NoseAction):
    """
    A base class for NoseActions that change the speed of simulated calibration
    procedures. The speed multiplier is used is equal to radioValue.
    """
    radioGroupName = 'speed factor'
    requiresSimulation = True

    def run(self):
        self.system.speedFactor = float(self.radioValue)


class SetCalibrationSpeedNormalAction(SetCalibrationSpeedAction):
    """The calibration procedure uses its normal speed."""
    name = 'setCalibrationSpeedNormal'
    text = gettext('_Normal Speed')
    radioActive = True
    radioValue = 1
    requiresSimulation = False

class SetCalibrationSpeed5Action(SetCalibrationSpeedAction):
    """The calibration procedure is sped up by a factor of five."""
    name = 'setCalibrationSpeed5'
    text = gettext('Speed Factor _5')
    radioValue = 5

class SetCalibrationSpeed10Action(SetCalibrationSpeedAction):
    """The calibration procedure is sped up by a factor of ten."""
    name = 'setCalibrationSpeed10'
    text = gettext('Speed Factor _10')
    radioValue = 10

class SetCalibrationSpeed25Action(SetCalibrationSpeedAction):
    """The calibration procedure is sped up by a factor of twenty-five."""
    name = 'setCalibrationSpeed25'
    text = gettext('Speed Factor _25')
    radioValue = 25


class CollectGarbageAction(NoseAction):
    """
    Runs garbage collection, and displays a warning if there are any
    unreachable objects that cannot be freed. (See the documentation of
    gc.garbage for an explanaition of why such objects might exist.)
    """
    name = 'collectGarbage'
    text = gettext('Collect _Garbage')
    stock = gtk.STOCK_DELETE

    def run(self):
        # TODO: Move body elsewhere?
        gc.collect()
        garbage = gc.garbage

        if garbage:
            txt = gettext('The following unreachable objects cannot be freed:')
            for g in garbage:
                txt += '\n%s\n' % g
            dialog = gtk.MessageDialog(
                mainWindowHandler.window,
                0,
                gtk.MESSAGE_WARNING,
                gtk.BUTTONS_CLOSE,
                txt)
            dialog.run()
            dialog.destroy()


###############################################################################
# MAGIC PYROMETER                                                             #
###############################################################################

class MagicPyrometer(object):

    def __init__(self, system):
        self.simulation = system._interface
        self.window = gtk.Window()
        self.window.set_size_request(250, 100)
        self.window.set_title(gettext('Magic Pyrometer'))
        self.label = gtk.Label()
        self.window.add(self.label)
        gobject.timeout_add(250, self._update)

    def _update(self):
        temperature = self.simulation.temperature
        self.label.set_text('%.0f °C' % temperature)
        return self.window.has_user_ref_count

    def show(self):
        self.window.show_all()
        self.window.show()
