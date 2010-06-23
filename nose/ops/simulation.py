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
This module contains the :class:`SimulatedDeviceInterface` class.
"""

import math
import numpy
import time

import ops.error


class SimulatedDeviceInterface(object):
    """
    A drop-in replacement for :class:`~ops.interface.DeviceInterface` that
    simulates communication with an FCI-7011 fiber coupler production system,
    so that the application can be tested without access to an actual system.
    """

    def __init__(self):
        self._heatingCurrent = i = 0.0
        self._heaterTargetPosition = 0.0
        self._speedFactor = 1.0

        # The time the heating current, heater target position, or speed
        # factor were last changed, and the heating temperature and heater
        # position at that time. Used to calculate the current heating
        # temperature and heater position.
        self._startingTime = 0.0
        self._startingTemperature = self.finalTemperatureFromCurrent(i)
        self._heaterStartingPosition = self._heaterTargetPosition


    def _setNewStart(self):
        """
        Records the current time, heating temperature, and heater position as
        the starting time, starting temperature, and starting position used
        to calculate the heating temperature and heater position. This method
        must be called each time the heating current, heater target position
        or speed factor change.
        """
        now = time.time()
        self._startingTemperature = self._getTemperature(now)
        self._heaterStartingPosition = self._getHeaterPosition(now)
        self._startingTime = now   # This must happen last!


    ###########################################################################
    # SIMULATION PARAMETERS                                                   #
    ###########################################################################

    # An instance of :class:`numpy.poly1d` that determines the temperature
    # (in °C) the simulated device's heater will reach, but not exceed,
    # for a given heating current (in mA). THIS IS A NON-EXTRACTABLE COMMENT.
    finalTemperatureFromCurrent = numpy.poly1d(
        [0.0052, -0.28, 3.3, 76.0, 0.0])

    # An instance of :class:`numpy.poly1d` that determines the simulated
    # device's temperature sensor voltage (in V) for the given heating
    # temperature (in °C). THIS IS A NON-EXTRACTABLE COMMENT.
    voltageFromTemperature = numpy.poly1d(
        [3.2e-12, -6.8e-9, 5.2e-6, -1.4e-3, 0.0])

    #: A time constant used to control the speed the simulated device's heating
    #: temperature changes. Inversely proportional to that speed.
    tau = 100.0

    #: The speed the simulated device's heater can move at, expressed as the
    #: fraction of the distance from its rearmost position to its foremost
    #: position it covers in one second. (Values greater than ``1.0`` are
    #: possible if the heater can cover that distance in less than one second.)
    #:
    #: This assumes that the heater can accelerate and decelerate instantly,
    #: which is unrealistic but should suffice for simulation purposes.
    heaterMovementRate = 0.1


    ###########################################################################
    # HEATING                                                                 #
    ###########################################################################

    @property
    def heatingCurrent(self):
        """
        The simulated device's heating current, in mA. Read-only. To change the
        heating current, use the :meth:`startHeatingWithCurrent` method.
        """
        return self._heatingCurrent


    @property
    def temperatureSensorVoltage(self):
        """
        The simulated system's temperature sensor's voltage, in V. Read-only.

        .. note::

            The value of this property assumes that the temperature sensor is
            able to get an accurate temperature reading, which will not always
            be the case for an actual device.

        The temperature sensor voltage is calculated from :attr:`temperature`
        each time this property is accessed. As a result, it may be distorted
        by changes to the system clock and by leap seconds.
        """
        return self.voltageFromTemperature(self.temperature)


    @property
    def temperature(self):
        """
        The simulated system's heating temperature temperature, in °C.
        Read-only.

        .. note::

            This property exists for testing purposes only. It is not provided
            by the real :class:`~ops.interface.DeviceInterface` class, since
            an actual device's heating temperature is not readily available
            (but see the :attr:`~ops.system.ProductionSystem.temperature`
            property of :class:`~ops.system.ProductionSystem`.)

        The temperature is calculated from the time the heating current was
        last changed and the temperature at that time each time this property
        is accessed. As a result, it may be distorted by changes to the system
        clock and by leap seconds.
        """
        return self._getTemperature(time.time())


    def _getTemperature(self, wallclockTime):
        """
        Returns the simulated device's heating temperature at the given time.

        This method exits to make simplify testing this class; without it,
        :meth:`startHeatingWithCurrent` and :meth:`startHeaterMovement` would
        call :func:`time.time` more than once, which would make it impossible
        to feed the class artificial timestamps without in-depth knowledge of
        its implementation details.
        """
        T0 = self._startingTemperature
        T1 = self.finalTemperatureFromCurrent(self.heatingCurrent)
        t  = wallclockTime - self._startingTime
        assert t >= 0.0
        return T0 + (T1 - T0) * (1 - math.exp(-t / self.tau))


    def startHeatingWithCurrent(self, current):
        """
        Sets the simulated device's heating current to `current`, in mA.
        """
        if current >= 0.0:
            self._setNewStart()
            self._heatingCurrent = current
        else:
            raise ops.error.InvalidHeatingCurrentError(current)


    ###########################################################################
    # HEATER MOVEMENT                                                         #
    ###########################################################################

    @property
    def heaterPosition(self):
        """
        The position of the simulated device's heater, as a fraction of the
        distance between rearmost position (``0.0``) and foremost position
        (``1.0``). Read-only. To move the heater to another position, use the
        :meth:`startHeaterMovement` method.

        The position is calculated from the time the last movement command was
        issued and the position of the heater at that time each time this
        property is accessed. As a result, it may be distorted by changes to
        the system clock and by leap seconds.
        """
        return self._getHeaterPosition(time.time())


    def _getHeaterPosition(self, wallclockTime):
        """
        Returns the simulated device's heater position at the given time.

        This method exits to make simplify testing this class; without it,
        :meth:`startHeatingWithCurrent` and :meth:`startHeaterMovement` would
        call :func:`time.time` more than once, which would make it impossible
        to feed the class artificial timestamps without in-depth knowledge of
        its implementation details.
        """
        p0 = self._heaterStartingPosition
        p1 = self._heaterTargetPosition
        t = wallclockTime - self._startingTime
        assert t >= 0.0
        change =  t * self.heaterMovementRate
        if p0 < p1:
            return min(p1, p0 + change)
        else:
            return max(p1, p0 - change)


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
        """
        if 0.0 <= targetPosition <= 1.0:
            self._setNewStart()
            self._heaterTargetPosition = targetPosition
        else:
            raise ops.error.InvalidHeaterPositionError(targetPosition)


    ###########################################################################
    # TESTING                                                                 #
    ###########################################################################

    @property
    def isSimulation(self):
        """
        Indicates whether this class just simulates communication with a
        device. (It does.) Immutable.
        """
        return True


    @property
    def speedFactor(self):
        """
        The factor by which the simulation is sped up. Setting this property
        to, say, ``5.0`` greatly reduces the time required to test the
        application. Needless to say, the property is not provided by the
        real :class:`~ops.interface.DeviceInterface` class. Mutable.
        """
        return self._speedFactor


    @speedFactor.setter
    def speedFactor(self, newSpeedFactor):
        # The setter for :attr:`speedFactor`.
        if newSpeedFactor > 0.0:
            self._setNewStart()
            self.tau *= self._speedFactor / newSpeedFactor
            self.heaterMovementRate *= newSpeedFactor / self._speedFactor
            self._speedFactor = newSpeedFactor
        else:
            raise ValueError('the speed factor cannot be negative')

