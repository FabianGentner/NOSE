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
This module contains the :class:`DeviceInterface` class.
"""

class DeviceInterface(object):
    """
    A class that is responsible for communicating with the FCI-7011 fiber
    coupler production system. Not yet implemented.

    In order to test the application without access to an actual production
    system, :class:`~ops.simulation.SimulatedDeviceInterface`, a drop-in
    replacement for this class which just simulates communication with a
    production system is provided.
    """

    def __init__(self):
        self._heatingCurrent = 0.0
        self._heaterTargetPosition = 0.0


    ###########################################################################
    # HEATING                                                                 #
    ###########################################################################

    @property
    def heatingCurrent(self):
        """
        The device's heating current, in mA. Read-only. To change the
        heating current, use the :meth:`startHeatingWithCurrent` method.
        """
        return self._heatingCurrent


    @property
    def temperatureSensorVoltage(self):
        """
        The system's temperature sensor's voltage, in V. Read-only.
        Not yet implemented.
        """
        raise NotImplementedError()


    def startHeatingWithCurrent(self, current):
        """
        Sets the device's heating current to `current`, in mA.
        Not yet implemented.
        """
        raise NotImplementedError()


    ###########################################################################
    # HEATER POSITION                                                         #
    ###########################################################################

    @property
    def heaterPosition(self):
        """
        The position of the simulated device's heater, as a fraction of the
        distance between rearmost position (``0.0``) and foremost position
        (``1.0``). Read-only. To move the heater to another position, use the
        :meth:`startHeaterMovement` method.

        Not yet implemented.
        """
        raise NotImplementedError()
        # TODO: Is this information actually available?


    @property
    def heaterTargetPosition(self):
        """
        The position the heater is supposed to be at, as a fraction of the
        distance between rearmost position (``0.0``) and foremost position
        (``1.0``).

        If :attr:`heaterTargetPosition` is not equal to :attr:`heaterPosition`,
        the heater is still moving to its target position.

        Read-only. To change the heater's target position, use the
        :meth:`startHeaterMovement` method.
        """
        return self._heaterTargetPosition


    def startHeaterMovement(self, targetPosition):
        """
        Moves the heater to the given position, expressed as a fraction of the
        distance between rearmost position (``0.0``) and foremost position
        (``1.0``).

        *This method is asynchronous.* Moving the heater can take several
        seconds, but this method returns immediately.

        To check which position the heater is currently moving to, use
        :attr:`heaterTargetPosition`; to get its actual position use
        :attr:`heaterPosition`.

        Not yet implemented.
        """
        self._heaterTargetPosition = position
        raise NotImplementedError()


    ###########################################################################
    # GENERAL ATTRIBUTES                                                      #
    ###########################################################################

    @property
    def isSimulation(self):
        """
        Indicates whether this class just simulates communication with a
        device. (It doesn't.) Immutable.
        """
        return False
