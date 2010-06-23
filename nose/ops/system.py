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
This module contains the :class:`ProductionSystem` class -- the cornerstone of
the application.
"""

import math

from ops.event import *
from ops.calibration.event import *

import ops.error
import ops.simulation
import ops.calibration.data
import ops.calibration.fake
import ops.calibration.manager
import util



def systemProperty(name):
    internalName = '_' + name
    def get(self):
        return getattr(self, internalName)
    def set(self, value):
        if value != getattr(self, internalName):
            setattr(self, internalName, value)
            self.mediator.noteEvent(SystemPropertiesChanged(self, name))
    return property(get, set)



class ProductionSystem(object):
    """
    A class that provides high-level control over an FCI-7011 fiber coupler
    production system (the :term:`device`). Each instance of this class
    wraps a :class:`~ops.interface.DeviceInterface` object (which handles the
    communication with the device) and complements the low-level functionality
    it provides with a number of high-level services:

    * Instances hold *calibration data* for the device. If this
      calibration data is complete, clients can interact with the device in
      terms of heating temperatures rather than temperature sensor voltages
      and heating currents by using its :attr:`temperature` property and
      :meth:`startHeatingToTemperature` method. The calibration data itself
      is stored in a :class:`~ops.calibration.data.CalibrationData` object,
      and can be accessed using the :attr:`calibrationData` property.

      The necessary data can be gathered by performing a :term:`calibration
      procedure`, which requires the application's user to take a series of
      temperature measurements, and may take several hours. A calibration
      procedure can be started by calling :meth:`startCalibration`.
      See the documentation for :mod:`ops.calibration.manager` for further
      information

      To check whether an instance has a complete set of calibration data for
      its device, use :attr:`isCalibrated`.

    * Instances monitor the device's temperature and temperature sensor
      voltage. If either exceeds its safe limits (:attr:`maxSafeTemperature`
      and :attr:`maxSafeTemperatureSensorVoltage`, respectively), the instance
      is switched into its :term:`safe mode`. In safe mode, the device's
      heating current is set to :attr:`heatingCurrentInSafeMode`, and the
      instance's :attr:`isInSafeMode` flag is set. The instance leaves safe
      mode when a new new heating procedure is started.

    * Instances can be locked. While an instance is locked, clients cannot
      perform any operations on the device without providing the appropriate
      key. This ensures that different operations do not interfere with each
      other.

      To lock or unlock an instance, use the :meth:`lock` and :meth:`unlock`
      methods. To check whether an instance is locked, use the :attr:`isLocked`
      property.

    An :class:`ops.simulation.SimulatedDeviceInterface` object can be
    substituted for the :class:`~ops.interface.DeviceInterface` in order to
    test the application without using an actual device.
    """

    ###########################################################################
    # GENERAL ATTRIBUTES                                                      #
    ###########################################################################

    def __init__(self, mediator, interface=None):
        """
        Instantiates a new instance of this class.

        `mediator` is used to set :attr:`mediator`.

        `interface` is the :class:`~ops.interface.DeviceInterface` the
        instance uses to communicate with the device it controls, a
        :class:`~ops.simulation.SimulatedDeviceInterface`, or ``None``,
        in which case a new :class:`~ops.simulation.SimulatedDeviceInterface`
        object is used.
        """
        self._mediator = mediator

        if interface is None:
            self._interface = ops.simulation.SimulatedDeviceInterface()
        else:
            self._interface = interface

        self._key = None
        self._calibrationData = None
        self._calibrationManager = None
        self._isInSafeMode = False
        self._targetTemperature = None
        self._heaterTargetPosition = self._interface.heaterPosition

        self._maxHeatingCurrent = 28.0
        self._maxSafeTemperatureSensorVoltage = 6.7
        self._maxSafeTemperature = 1700.0
        self._heatingCurrentInSafeMode = 4.0
        self._heatingCurrentWhileIdle = 4.0

        # Do not assign directly to _calibrationData here! The inital
        # CalibrationData object must have its system set!
        self.calibrationData = ops.calibration.data.CalibrationData()

        mediator.addTimeout(
            ProductionSystem.monitorInterval, self._monitorSafeOperation)


    @property
    def mediator(self):
        """
        The :class:`~gui.mediator.Mediator` the instance uses to communicate
        with the GUI, or an object that provides a compatible interface.
        Immutable.
        """
        return self._mediator


    ###########################################################################
    # SYSTEM PROPERTIES                                                       #
    ###########################################################################

    #: The highest legal heating current, in mA.
    maxHeatingCurrent = systemProperty('maxHeatingCurrent')

    #: The highest safe temperature sensor voltage, in V. If this voltage is
    #: exceeded the instance switches into its safe mode. Having a highest
    #: safe temperature sensor voltage as well as a highest safe heating
    #: temperature allows monitoring the device even if it is uncalibrated.
    maxSafeTemperatureSensorVoltage = systemProperty(
        'maxSafeTemperatureSensorVoltage')

    #: The highest safe heating temperature, in °C. If this temperature is
    #: exceeded, the instance switches into its safe mode. The device needs
    #: to be calibrated for this to work.
    maxSafeTemperature = systemProperty('maxSafeTemperature')

    #: The heating current used in safe mode, in mA.
    heatingCurrentInSafeMode = systemProperty('heatingCurrentInSafeMode')

    #: The heating current used when the device is idle, in mA.
    heatingCurrentWhileIdle = systemProperty('heatingCurrentWhileIdle')


    ###########################################################################
    # LOCKING                                                                 #
    ###########################################################################

    @property
    def isLocked(self):
        """
        Indicates whether the instance is locked. Read-only. To lock or unlock
        the instance, use the :meth:`lock` and :meth:`unlock` methods.
        """
        return self._key != None


    def lock(self, key):
        """
        Locks the instance with the given key. While it is locked, clients
        cannot perform any operations on the device without providing the
        appropriate key.

        Any object other than ``None`` may be used as the key. If the instance
        is already locked, a :exc:`~ops.error.SystemLockedError` is raised.
        """
        if self._key is not None:
            raise ops.error.SystemLockedError()
        elif key is None:
            raise ValueError('keys may not be None')
        else:
            self._key = key


    def unlock(self, key):
        """
        Unlocks the instance, using the given key. If the instance
        is not locked, a :exc:`~ops.error.SystemNotLockedError` is raised.
        If a key other than the one used to lock the instance is passed,
        a :exc:`~ops.error.WrongKeyError` is raised.
        """
        if self._key == None:
            raise ops.error.SystemNotLockedError()
        elif key != self._key:
            raise ops.error.WrongKeyError()
        else:
            self._key = None


    def _tryKey(self, key):
        """
        Checks whether the given key is the one used to lock the instance,
        and raises an exception if it isn't.
        """
        if key == None and self._key != None:
            raise ops.error.SystemLockedError()
        if key != None and self._key == None:
            raise ops.error.SystemNotLockedError()
        if key != self._key:
            raise ops.error.WrongKeyError()


    ###########################################################################
    # CALIBRATION                                                             #
    ###########################################################################

    @property
    def isCalibrated(self):
        """
        Indicates whether the instance has complete calibration data for the
        device. This is always ``False`` while a calibration procedure is
        underway. Read -only.
        """
        return self.calibrationData.isComplete and not self.isBeingCalibrated


    @property
    def isBeingCalibrated(self):
        """
        Indicates whether a calibration procedure is underway. Read-only.
        """
        return self.calibrationManager is not None


    @property
    def calibrationManager(self):
        """
        The :class:`~ops.calibration.manager.CalibrationManager` that is
        managing the ongoing calibration procedure of the device the instance
        controls, or ``None`` if the device is not being calibrated. Read-only.
        """
        return self._calibrationManager


    @property
    def calibrationData(self):
        """
        A :class:`~ops.calibration.data.CalibrationData` object that holds
        the resuts of the calibration procedure of the device the instance
        controls.

        May be modified, but the new calibration data object may not be
        currently used by another :class:`ProductionSystem` (that is, its
        :attr:`~ops.calibration.data.CalibrationData.system` property must
        be ``None``), or an :exc:`~util.ApplicationError` is raised.
        """
        return self._calibrationData


    @calibrationData.setter
    def calibrationData(self, newCalibrationData):
        # The setter for the :attr:`calibrationData` property.
        if newCalibrationData is None:
            raise ValueError('calibrationData may not be None')
        elif newCalibrationData is not self._calibrationData:
            oldCalibrationData = self._calibrationData
            self._calibrationData = newCalibrationData
            newCalibrationData.system = self

            # Special case: when setting the initial CalibrationData object,
            # _calibrationData is still None.
            if oldCalibrationData is not None:
                oldCalibrationData.system = None

            self._mediator.noteEvent(
                CalibrationDataChanged(self, newCalibrationData))


    def startCalibration(self, currents):
        """
        Starts a :term:`calibration procedure`. `currents` is a list of the
        heating currents (in mA) for which measurements are to be taken.
        The actual work is done by
        :class:`ops.calibration.manager.CalibrationManager`.
        See that class for further documentation.

        *This method is asynchronous.* The calibration procedure itself may
        take several hours to complete, but the method returns immediately.

        The instance is locked for the duration of the calibration procedure.
        If the instance is already locked when this method is called, a
        :exc:`~ops.error.SystemLockedError` is raised.

        During the calibration procedure, the application's user needs to be
        available to take a series of temperature measurements.
        """
        if self.isLocked:
            raise ops.error.SystemLockedError()
        else:
            self.mediator.addListener(
                self._calibrationOverListener, CalibrationOver)

            if self.testingUseFakeCalibration:
                m = ops.calibration.fake.FakeCalibrationManager(self, currents)
            else:
                m = ops.calibration.manager.CalibrationManager(self, currents)

            self._calibrationManager = m
            self._calibrationManager.startCalibration()


    def abortCalibration(self):
        """
        Aborts the ongoing calibration procedure.
        """
        self._calibrationManager.abortCalibration()


    def _calibrationOverListener(self, event):
        """
        Called when a :class:`~ops.calibration..event.CalibrationOver` event
        is sent. Clears :attr:`calibrationManager`.
        """
        self._calibrationManager = None
        self.mediator.removeListener(
            self._calibrationOverListener, CalibrationOver)


    ###########################################################################
    # MONITORING                                                              #
    ###########################################################################

    #: The interval the temperature is monitored in, in milliseconds.
    #: This is a class attribute. Setting it on an instance has no effect.
    monitorInterval = 1000


    # ISSUE: If operating the heater at heatingCurrentInSafeMode is still
    #        unsafe, monitoring doesn't help. We could turn the device off
    #        if it continues to trip the monitor N seconds after being put
    #        into safe mode.

    def _monitorSafeOperation(self):
        """
        Switches the instance into its safe mode if heating temperature or
        temperature sensor voltage exceed their safe limits. Called once
        every :attr:`monitorInterval` milliseconds.
        """
        if self._isUnsafe(self.temperatureSensorVoltage, self.temperature):
            self.enterSafeMode()

        # This method needs to return ``True`` so that it is called again.
        return True


    def _isUnsafe(self, voltage, temperature):
        """
        Indicates whether the given temperature sensor voltage (in V) or
        heating temperature (in °C) exceed their safe range. `temperature`
        may be ``None``.
        """
        if voltage == None:
            raise ValueError()
        else:
            return (voltage > self.maxSafeTemperatureSensorVoltage
                or (temperature is not None
                and temperature > self.maxSafeTemperature))


    def enterSafeMode(self):
        """
        Switches the instance into its :term:`safe mode`. In safe mode, the
        device's heating current is set to :attr:`heatingCurrentInSafeMode`,
        and the instance's :attr:`isInSafeMode` flag is set. The instance
        leaves safe mode when a new new heating procedure is started.

        Calling this method on a locked instance does not require a key;
        operations must be able to deal with the fact that the instance may
        unexpectedly enter safe mode while they are running. Entering
        safe mode does not unlock the instance, however.
        """
        # This method will be called repeatedly until the temperature or
        # temperature sensor voltage no longer exceeds the safe limits.
        if self.heatingCurrent > self.heatingCurrentInSafeMode:
            self.startHeatingWithCurrent(
                self.heatingCurrentInSafeMode, self._key)
        self._isInSafeMode = True


    @property
    def isInSafeMode(self):
        """
        Indicates whether the instance is in its safe mode. Read-only.
        """
        return self._isInSafeMode


    ###########################################################################
    # HEATING                                                                 #
    ###########################################################################

    @property
    def heatingCurrent(self):
        """
        The device's heating current, in mA. Read-only. To change the
        heating current, use the :meth:`startHeatingWithCurrent` method.
        """
        return self._interface.heatingCurrent


    @property
    def temperatureSensorVoltage(self):
        """
        The voltage reported by the temperature sensor, in V. Read-only.

        In most cases, clients will want to use :attr:`temperature` instead.

        .. note::

            If the heater is not in its foremost position (see
            :attr:`heaterPosition`), the returned voltage will not be an
            accurate reflection of the heater's temperature. If the user
            has moved the temperature sensor aside, it will be unrelated
            to the heater's temperature.
        """
        return self._interface.temperatureSensorVoltage


    @property
    def temperature(self):
        """
        The heating temperature that corresponds to the measured temperature
        sensor voltage, in °C, or ``None`` if the device isn't calibrated.
        Read-only.

        .. note::

            The returned temperature is only accurate if the temperature sensor
            can get an accurate reading. If the heater is not in its foremost
            position (see :attr:`heaterPosition`), the returned temperature
            will be inaccurate. If the user has moved the temperature sensor
            aside, it will be unrelated to the actual heating temperature.
        """
        if self.isCalibrated:
            voltage = self.temperatureSensorVoltage
            return self.calibrationData.getTemperatureFromVoltage(voltage)
        else:
            return None


    @property
    def targetTemperature(self):
        """
        The temperature the heater is being heated to, in °C, or ``None`` if
        it is not being heated to a particular temperature.

        Read-only. To change the target temperature, or start heating towards a
        particular temperature, use the :meth:`startHeatingToTemperature`
        method.

        Changing the heating current using :meth:`startHeatingWithCurrent`
        resets this property to ``None``.
        """
        return self._targetTemperature


    @property
    def minTargetTemperature(self):
        """
        The lowest target temperature that can be passed to
        :meth:`startHeatingToTemperature`, in °C, or ``None`` if the
        device is not calibrated.

        The value is equal to the lowest temperature measured during the
        calibration procedure. Read-only.
        """
        if self.isCalibrated:
            return min(self.calibrationData.temperatures)
        else:
            return None



    @property
    def maxTargetTemperature(self):
        """
        The highest target temperature that can be passed to
        :meth:`startHeatingToTemperature`, in °C, or ``None`` if the
        device is not calibrated.

        The value is equal to the lowest of :attr:`maxSafeTemperature`, the
        temperature that can be reached with a heating current equal to
        :attr:`maxHeatingCurrent`, or the highest temperature measured
        during the calibration procedure. Read-only.
        """
        if not self.isCalibrated:
            return None

        cd = self.calibrationData
        maxI = self.maxHeatingCurrent
        result = min(
            self.maxSafeTemperature,
            cd.getFinalTemperatureFromCurrent(maxI),
            max(cd.temperatures))

        # HACK: At this point, currentFromTargetTemperature(result) may be
        # greater than maxHeatingCurrent, and hence invalid, since, given
        # sufficiently wonky calibration data, it is not guaranteed that
        # currentFromTargetTemperature(finalTemperatureFromCurrent(i)) == i.
        # We fix this by trying lower results until one fits, or until result
        # should have been reduced to a third of its original value, in which
        # case something is probably very wrong, and we give up to avoid
        # entering an endless loop (which would be bad).
        for attempt in xrange(111):
            if cd.getCurrentFromTargetTemperature(result) <= maxI:
                break
            else:
                result *= 0.99
        else:
            raise util.ApplicationError('something seems to be very wrong')

        return result


    def isValidTargetTemperature(self, temperature):
        """
        Indicates whether the given temperature (in °C) can be passed to
        :meth:`startHeatingToTemperature`, that is, whether it lies between
        :attr:`minTargetTemperature` and :attr:`maxTargetTemperature`.

        If the device is not calibrated, a :exc:`~ops.error.NotCalibratedError`
        is raised.
        """
        if not self.isCalibrated:
            raise ops.error.NotCalibratedError()
        else:
            return (self.minTargetTemperature <= temperature
                and temperature <= self.maxTargetTemperature)


    def startHeatingWithCurrent(self, current, key=None):
        """
        Sets the device's heating current to `current`, in mA. Also clears
        the :attr:`isInSafeMode` flag and sets :attr:`targetTemperature` to
        ``None``.

        If the instance is locked, the appropriate key must be passed,
        otherwise a :exc:`~ops.error.SystemLockedError` is raised.
        If the wrong key is passed, a :exc:`~ops.error.WrongKeyError` is
        raised. If a key is passed even though the instance is not locked,
        a :exc:`~ops.error.SystemNotLockedError` is raised.

        If `current` is negative or exceeds :attr:`maxHeatingCurrent`, an
        :exc:`~ops.error.InvalidHeatingCurrentError` is raised.
        """
        self._tryKey(key)
        if 0.0 <= current <= self.maxHeatingCurrent:
            self._isInSafeMode = False
            self._targetTemperature = None
            self._interface.startHeatingWithCurrent(current)
        else:
            raise ops.error.InvalidHeatingCurrentError(current)


    def startHeatingToTemperature(self, targetTemperature, key=None):
        """
        Sets the device's heating current to a value that should result in the
        heater reaching, but not exceeding, `targetTemperature`, in °C. The
        device must be calibrated for this method to be usable. Also clears the
        :attr:`isInSafeMode` flag and sets :attr:`targetTemperature` to
        `targetTemperature`.

        If the instance is locked, the appropriate key must be passed,
        otherwise a :exc:`~ops.error.SystemLockedError` is raised.
        If the wrong key is passed, a :exc:`~ops.error.WrongKeyError` is
        raised. If a key is passed even though the instance is not locked,
        a :exc:`~ops.error.SystemNotLockedError` is raised.

        If the device is not calibrated, a :exc:`~ops.error.NotCalibratedError`
        is raised.

        If `targetTemperature` is less than :attr:`minTargetTemperature` or
        greater then :attr:`maxTargetTemperature`, an
        :exc:`~ops.error.InvalidTargetTemperatureError` is raised.

        The temperature sensor is not used by the heating procedure started by
        this method at all. The current used is determined from the temperature
        measurements taken during the calibration procedure, and no
        second-guessing based on the temperature sensor voltages reported
        during the heating procedure takes place. This means this method
        is not affected by the issues mentioned in the documentation for the
        :attr:`temperature` property.

        *This method is asynchronous.* It will take some time for the heater
        to reach the target temperature, but the method will return
        immediately.
        """
        self._tryKey(key)
        if not self.isCalibrated:
            raise ops.error.NotCalibratedError()
        elif not self.isValidTargetTemperature(targetTemperature):
            raise ops.error.InvalidTargetTemperatureError(targetTemperature)
        else:
            cd = self.calibrationData
            current = cd.getCurrentFromTargetTemperature(targetTemperature)
            self.startHeatingWithCurrent(current, key)
            self._targetTemperature = targetTemperature   # Must happen last.


    def idle(self, key=None):
        """
        Sets the device's heating current to :attr:`heatingCurrentWhileIdle`.

        If the instance is locked, the appropriate key must be passed,
        otherwise a :exc:`~ops.error.SystemLockedError` is raised.
        If the wrong key is passed, a :exc:`~ops.error.WrongKeyError` is
        raised. If a key is passed even though the instance is not locked,
        a :exc:`~ops.error.SystemNotLockedError` is raised.
        """
        self.startHeatingWithCurrent(self.heatingCurrentWhileIdle, key)


    ###########################################################################
    # HEATER MOVEMENT                                                         #
    ###########################################################################

    @property
    def heaterPosition(self):
        """
        The position of the heater, as a fraction of the distance between
        rearmost position (``0.0``) and foremost position (``1.0``).
        Read-only. To move the heater to another position, use the
        :meth:`startHeaterMovement` method.
        """
        return self._interface.heaterPosition


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
        return self._interface.heaterTargetPosition


    def startHeaterMovement(self, targetPosition, key=None):
        """
        Moves the heater to the given position, expressed as a fraction of the
        distance between rearmost position (``0.0``) and foremost position
        (``1.0``).

        If the instance is locked, the appropriate key must be passed,
        otherwise a :exc:`~ops.error.SystemLockedError` is raised.
        If the wrong key is passed, a :exc:`~ops.error.WrongKeyError` is
        raised. If a key is passed even though the instance is not locked,
        a :exc:`~ops.error.SystemNotLockedError` is raised.

        If `targetPosition` is less than ``0.0`` or greater than ``1.0``,
        an :exc:`~ops.error.InvalidHeaterPositionError` is raised.

        *This method is asynchronous.* Moving the heater can take several
        seconds, but this method returns immediately.

        To check which position the heater is currently moving to, use
        :attr:`heaterTargetPosition`; to get its actual position use
        :attr:`heaterPosition`.
        """
        self._tryKey(key)
        self._interface.startHeaterMovement(targetPosition)


    ###########################################################################
    # TESTING                                                                 #
    ###########################################################################

    @property
    def isSimulation(self):
        """
        Indicates whether the device the instance controls is simulated;
        that is, whether it wraps
        a :class:`~ops.simulation.SimulatedDeviceInterface`
        or a :class:`~ops.interface.DeviceInterface`. Immutable.
        """
        return self._interface.isSimulation


    @property
    def speedFactor(self):
        """
        The factor by which all operations performed with the device are sped
        up. Setting this property to, say, ``5.0`` greatly reduces the time
        required to test the application. Mutable.

        This property is intended for testing purposes only. If the instance
        wraps a real :class:`~ops.interface.DeviceInterface`, any attempt
        to acess it raises a :exc:`~ops.error.RequiresSimulationError`.
        """
        if not self.isSimulation:
            raise ops.error.RequiresSimulationError()
        else:
            return self._interface.speedFactor


    @speedFactor.setter
    def speedFactor(self, newSpeedFactor):
        # The setter for :attr:`speedFactor`.
        if not self.isSimulation:
            raise ops.error.RequiresSimulationError()
        else:
            self._interface.speedFactor = newSpeedFactor


    def performMagicCalibration(self):
        """
        Creates a :class:`~ops.calibration.data.CalibrationData` object using
        the parameters of the :class:`~ops.simulation.SimulatedDeviceInterface`
        used by the instance, and assigns it to :attr:`calibrationData`.
        Unlike a real calibration procedure, magic calibration is instant.
        The :class:`~ops.calibration.manager.CalibrationManager` is not used.

        This method is intended for testing purposes only. If the instance
        wraps a real :class:`~ops.interface.DeviceInterface`, this method
        raises a :exc:`~ops.error.RequiresSimulationError`.

        Magic calibration will generate measurements for heating currents
        starting at :attr:`heatingCurrentWhileIdle` and increasing in steps
        of 2 mA until they would exceed :attr:`maxHeatingCurrent` or the
        temperature sensor voltage reached with this current would exceed
        :attr:`maxSafeTemperatureSensorVoltage`.
        """
        if not self.isSimulation:
            raise ops.error.RequiresSimulationError()

        self.calibrationData = cd = ops.calibration.data.CalibrationData()
        current = self.heatingCurrentWhileIdle

        while True:
            if current > self.maxHeatingCurrent:
                break

            temperature = self._interface.finalTemperatureFromCurrent(current)
            voltage = self._interface.voltageFromTemperature(temperature)

            if voltage > self.maxSafeTemperatureSensorVoltage:
                break

            cd.addMeasurement(current, voltage, temperature)
            current += 2.0


    # TODO: Comment
    testingUseFakeCalibration = False