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
Contains a number of exception classes for errors that can occur in the
:mod:`ops` package.

All exception classes in this module extend :exc:`util.ApplicationError`.
"""

import util


# TODO: Classes should perhaps be responsible for constructing their meassages
#       from data passed to them.

###############################################################################
# VALUE-RELATED ERRORS                                                        #
###############################################################################

class InvalidHeatingCurrentError(util.ApplicationError, ValueError):
    """
    Raised when one of the various :meth:`startHeatingWithCurrent` methods is
    called with an invalid current.
    """


class InvalidTargetTemperatureError(util.ApplicationError, ValueError):
    """
    Raised when :class:`~ops.system.ProductionSystem`'s
    :meth:`~ops.system.ProductionSystem.startHeatingToTemperature` method
    is called with an invalid heating temperature.
    """


class InvalidHeaterPositionError(util.ApplicationError, ValueError):
    """
    Raised when one of the various :meth:`startHeaterMovement` methods is
    called with an invalid target position.
    """


###############################################################################
# STATE-RELATED ERRORS                                                        #
###############################################################################

class NotCalibratedError(util.ApplicationError):
    """
    Raised by various methods of :class:`~ops.system.ProductionSystem` and
    :class:`~ops.calibration.data.CalibrationData` if they are called while
    the system has not yet been successfully calibrated.
    """


class RequiresSimulationError(util.ApplicationError):
    """
    Raised by :class:`~ops.system.ProductionSystem` when an operation that
    requires a :class:`~ops.simulation.SimulatedDeviceInterface` is performed
    on a system that wraps a real :class:`~ops.interface.DeviceInterface`.
    """


###############################################################################
# LOCKING-RELATED ERRORS                                                      #
###############################################################################

class LockingError(util.ApplicationError):
    """
    The base class for :exc:`SystemLockedError`, :exc:`SystemNotLockedError`,
    and :exc:`WrongKeyError`.
    """

class SystemLockedError(LockingError):
    """
    Raised when a client tries to start an operation on a locked
    :class:`~ops.system.ProductionSystem` without providing a key,
    or tries to lock a :class:`~ops.system.ProductionSystem` that
    is already locked.
    """


class SystemNotLockedError(LockingError):
    """
    Raised when a client provides a key when starting an operation
    on a :class:`~ops.system.ProductionSystem` that is not locked,
    or tries to unlock a :class:`~ops.system.ProductionSystem` that
    is not locked.
    """


class WrongKeyError(LockingError):
    """
    Raised when a client provides the wrong key when starting an operation
    on or unlocking a locked :class:`~ops.system.ProductionSystem`.
    """

