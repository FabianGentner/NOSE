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
A set of simple classes that are used to encapsulate the data associated with
the various events the :mod:`ops.calibration` package can send.

All classes in this module are immutable.
"""

from ops.event import Event


###############################################################################
# CALIBRATION STARTED                                                         #
###############################################################################

class CalibrationStarted(Event):
    """
    Used to indicate that a calibration procedure has just been started.
    """

    def __init__(self, system, manager):
        self._system = system
        self._manager = manager

    @property
    def calibrationIsRunning(self):
        # TODO: Document
        return True

    @property
    def system(self):
        """
        The :class:`~ops.system.ProductionSystem` that is being calibrated.
        """
        return self._system

    @property
    def manager(self):
        """
        The :class:`~ops.calibration.manager.CalibrationManager` that is
        responsible for the calibration procedure.
        """
        return self._manager


###############################################################################
# CALIBRATION OVER                                                            #
###############################################################################

class CalibrationOver(Event):
    """
    Used to indicate that a calibration procedure has just ended.
    """

    def __init__(self, system, manager, status, usedCurrents, unusedCurrents):
        self._system = system
        self._manager = manager
        self._status = status
        self._usedCurrents = usedCurrents
        self._unusedCurrents = unusedCurrents

    @property
    def calibrationIsRunning(self):
        # TODO: Document
        return False

    @property
    def system(self):
        """
        The :class:`~ops.system.ProductionSystem` that has been calibrated.
        """
        return self._system

    @property
    def manager(self):
        """
        The :class:`~ops.calibration.manager.CalibrationManager` that was
        responsible for the calibration procedure.
        """
        return self._manager

    @property
    def status(self):
        """
        A status code that indicates why the calibration procedure has ended.
        One of :data:`ops.calibration.manager.STATUS_ABORTED`,
        :data:`~ops.calibration.manager.STATUS_SAFE_MODE_TRIGGERED`,
        :data:`~ops.calibration.manager.STATUS_INVALID_CURRENT`, and
        :data:`~ops.calibration.manager.STATUS_FINISHED`.
        """
        return self._status

    @property
    def usedCurrents(self):
        # TODO: Document
        return self._usedCurrents

    @property
    def unusedCurrents(self):
        """
        A tuple of heating currents no measurements were taken for.
        If :attr:`status` is :data:`~ops.calibration.manager.STATUS_FINISHED`,
        the tuple will be empty.
        """
        return self._unusedCurrents


###############################################################################
# TEMPERATURE REQUESTED                                                       #
###############################################################################

class TemperatureRequested(Event):
    """
    Used to indicate that the user needs to take a temperature measurement
    before the calibration procedure can continue.
    """

    def __init__(self, manager, system, callback):
        self._manager = manager
        self._system = system
        self._callback = callback

    @property
    def temperatureRequested(self):
        # TODO: Document
        return True

    @property
    def manager(self):
        """
        The :class:`~ops.calibration.manager.CalibrationManager` that is
        responsible for the calibration procedure.
        """
        return self._manager

    @property
    def system(self):
        """
        The :class:`~ops.system.ProductionSystem` that is being calibrated.
        """
        return self._system

    @property
    def callback(self):
        """
        A function that can be called to report a temperature measurement,
        with the temperature (in °C) as argument. Calling this function after
        :attr:`manager` has sent a :class:`TemperatureRequestOver` event will
        raise an :class:`~util.ApplicationError`.
        """
        return self._callback


###############################################################################
# TEMPERATURE REQUEST OVER                                                    #
###############################################################################

class TemperatureRequestOver(Event):
    """
    Used to indicate that a temperature measurement previously requested
    with a :class:`TemperatureRequested` event is no longer required, either
    because it has already been supplied, or because the calibration procedure
    has ended.
    """

    def __init__(self, manager, system):
        self._manager = manager
        self._system = system

    @property
    def temperatureRequested(self):
        # TODO: Document
        return False

    @property
    def manager(self):
        """
        The :class:`~ops.calibration.manager.CalibrationManager` that is
        responsible for the calibration procedure.
        """
        return self._manager

    @property
    def system(self):
        """
        The :class:`~ops.system.ProductionSystem` that is being calibrated.
        """
        return self._system


###############################################################################
# CALIBRATION DATA CHANGED                                                    #
###############################################################################

class CalibrationDataChanged(Event):
    """
    Used to indicate that a :class:`~ops.calibration.data.CalibrationData`
    object has changed. If a calibration data object that is not currently
    used by a production system is changed, no event is sent.
    """

    def __init__(self, system, calibrationData):
        self._system = system
        self._calibrationData = calibrationData

    @property
    def system(self):
        """
        The :class:`~ops.system.ProductionSystem` the changed
        :class:`~ops.calibration.data.CalibrationData` object belongs to.
        """
        return self._system

    @property
    def calibrationData(self):
        """
        The changed :class:`~ops.calibration.data.CalibrationData` object
        itself. If a calibration data object is replaced with another,
        this is set to the new object.
        """
        return self._calibrationData


