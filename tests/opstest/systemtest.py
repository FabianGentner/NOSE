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
import unittest
import sys
import weakref

from ops.error import *
from ops.calibration.event import *
from ops.system import ProductionSystem
from stubs import DeviceInterfaceStub

import gui.mediator
import ops.calibration.data
import ops.calibration.manager
import ops.simulation
import test


class ProductionSystemTests(unittest.TestCase):
    """
    Tests for :class:`ops.system.ProductionSystem` class.
    """

    def setUp(self):
        self.mediator = gui.mediator.Mediator(logging=True)
        self.system = ProductionSystem(self.mediator)


    ###########################################################################
    # MISCELLANEOUS                                                           #
    ###########################################################################

    def testGC(self):
        """Makes sure the system is properly garbage-collected."""
        wr = weakref.ref(self.system)
        self.mediator.clearLog()
        self.system = None
        gc.collect()
        self.assertEqual(wr(), None)


    def testMedaitor(self):
        """Tests the :attr:`mediator` property."""
        self.assertEqual(self.system.mediator, self.mediator)
        self.assertRaises(AttributeError,
            setattr, self.system, 'mediator', gui.mediator.Mediator())


    def testInterfaceParameter(self):
        """Makes sure supplying an interface to the constructor works."""
        mediator = gui.mediator.Mediator()
        interface = ops.simulation.SimulatedDeviceInterface()
        system = ProductionSystem(mediator, interface)
        self.assertEqual(system._interface, interface)


    def testInterfaceParameterDefault(self):
        """Test the default for the constructor's interface parameter."""
        self.assertTrue(isinstance(
            self.system._interface, ops.simulation.SimulatedDeviceInterface))


    ###########################################################################
    # LOCKING                                                                 #
    ###########################################################################

    def testIsLocked(self):
        """Tests the :attr:`isLocked` parameter."""
        self.assertFalse(self.system.isLocked)

        self.system.lock(23)
        self.assertTrue(self.system.isLocked)

        self.system.unlock(23)
        self.assertFalse(self.system.isLocked)

        self.assertRaises(AttributeError,
            setattr, self.system, 'isLocked', True)


    def testLock(self):
        """Tests the :meth:`lock` method."""
        self.assertRaises(ValueError, self.system.lock, None)
        self.assertFalse(self.system.isLocked)

        for key in (42, 0, 0.0, [], (), {}, False):
            self.system.lock(key)
            self.assertTrue(self.system.isLocked)
            self.system.unlock(key)

        self.system.lock(42)

        self.assertRaises(SystemLockedError, self.system.lock, 1)
        self.assertRaises(SystemLockedError, self.system.lock, 42)
        self.assertRaises(SystemLockedError, self.system.lock, None)
        self.assertTrue(self.system.isLocked)


    def testUnlock(self):
        """Tests the :meth:`unlock` method."""
        self.assertRaises(SystemNotLockedError, self.system.unlock, 42)

        self.system.lock(42)
        self.assertRaises(WrongKeyError, self.system.unlock, 43)
        self.assertRaises(WrongKeyError, self.system.unlock, None)
        self.assertTrue(self.system.isLocked)

        self.system.unlock(42)
        self.assertFalse(self.system.isLocked)


    ###########################################################################
    # CALIBRATION                                                             #
    ###########################################################################

    def testIsCalibrated(self):
        """Tests the :attr:`isCalibrated` property."""
        self.assertFalse(self.system.isCalibrated)

        self.system.performMagicCalibration()
        self.assertTrue(self.system.isCalibrated)

        self.system.startCalibration([12.0])
        self.assertFalse(self.system.isCalibrated)

        self.system.abortCalibration()
        self.assertTrue(self.system.isCalibrated)

        self.system.calibrationData = ops.calibration.data.CalibrationData()
        self.assertFalse(self.system.isCalibrated)

        self.assertRaises(AttributeError,
            setattr, self.system, 'isCalibrated', True)


    def testIsBeingCalibrated(self):
        """Test the :attr:`isBeingCalibrated` property."""
        self.assertFalse(self.system.isBeingCalibrated)

        self.system.startCalibration([12.0])
        self.assertTrue(self.system.isBeingCalibrated)

        self.system.abortCalibration()
        self.assertFalse(self.system.isBeingCalibrated)

        self.assertRaises(AttributeError,
            setattr, self.system, 'isBeingCalibrated', True)


    def testCalibrationManager(self):
        """Tests the :attr:`calibrationManager` property."""
        self.assertEqual(self.system.calibrationManager, None)

        self.system.startCalibration([12.0])
        self.assertNotEqual(self.system.calibrationManager, None)

        self.system.abortCalibration()
        self.assertEqual(self.system.calibrationManager, None)

        self.assertRaises(AttributeError,
            setattr, self.system, 'calibrationManager', None)


    def testCalibrationData(self):
        """Tests the :attr:`calibrationData` property."""
        self.assertNotEqual(self.system.calibrationData, None)

        oldCD = self.system.calibrationData
        newCD = ops.calibration.data.CalibrationData()
        eventCount = len(self.mediator.eventsNoted)

        # Should habe no effect.
        self.system.calibrationData = oldCD
        self.assertTrue(self.system.calibrationData is oldCD)
        self.assertTrue(oldCD.system is self.system)
        self.assertEqual(len(self.mediator.eventsNoted), eventCount)

        self.system.calibrationData = newCD
        self.assertTrue(self.system.calibrationData is newCD)
        self.assertTrue(oldCD.system is None)
        self.assertTrue(newCD.system is self.system)
        event = self.mediator.eventsNoted[-1]
        self.assertEqual(event, CalibrationDataChanged(self.system, newCD))

        self.assertRaises(ValueError,
            setattr, self.system, 'calibrationData', None)
        self.assertEqual(self.system.calibrationData, newCD)
        self.assertTrue(self.mediator.eventsNoted[-1] is event)


    def testStartCalibration(self):
        """Tests the :meth:`startCalibration` method."""
        self.system.lock(23)

        self.assertRaises(SystemLockedError, self.system.startCalibration, [4])
        self.assertFalse(self.mediator.hasListener(
            self.system._calibrationOverListener, CalibrationOver))

        self.system.unlock(23)

        self.system.startCalibration([4.0])
        self.assertTrue(self.system.isLocked)
        self.assertTrue(self.system.calibrationManager.isRunning)
        self.assertTrue(self.mediator.hasListener(
            self.system._calibrationOverListener, CalibrationOver))

        self.system.abortCalibration()


    def testAbortCalibration(self):
        """Tests the :meth:`abortCalibration` method."""
        self.system.startCalibration([4.0])
        cm = self.system.calibrationManager

        self.system.abortCalibration()
        self.assertFalse(self.system.isLocked)
        self.assertEquals(self.system.calibrationManager, None)
        self.assertFalse(cm.isRunning)
        self.assertFalse(self.mediator.hasListener(
            self.system._calibrationOverListener, CalibrationOver))


    ###########################################################################
    # MONITORING                                                              #
    ###########################################################################

    def testMonitoringCallbackSetup(self):
        """Checks that the monitoring callback is set up correctly."""
        monitorInterval = ProductionSystem.monitorInterval
        try:
            ProductionSystem.monitorInterval = monitorInterval * 10
            self.mediator = gui.mediator.Mediator(logging=True)

            self.system = ProductionSystem(self.mediator)
            timeout, weakMethod = self.mediator.timeoutsAdded[-1]
            self.assertEqual(timeout, monitorInterval * 10)
            self.assertTrue(
                weakMethod.isSameMethod(self.system._monitorSafeOperation))
        finally:
            ProductionSystem.monitorInterval = monitorInterval


    def testMonitorSafeOperation(self):
        """Tests the :meth:`_monitorSafeOperation` method."""
        self.system.enterSafeMode = logger = test.CallLogger()

        self.system._isUnsafe = lambda u, t: False
        self.assertTrue(self.system._monitorSafeOperation())
        self.assertEqual(logger.log, [])

        self.system._isUnsafe = lambda u, t: True
        self.assertTrue(self.system._monitorSafeOperation())
        self.assertEqual(logger.log, [()])
        self.assertTrue(self.system._monitorSafeOperation())
        self.assertEqual(logger.log, [(), ()])

        self.system._isUnsafe = lambda u, t: False
        self.assertTrue(self.system._monitorSafeOperation())
        self.assertEqual(logger.log, [(), ()])


    def testIsUnsafe(self):
        """Tests the :meth:`_isUnsafe` method."""
        maxU = self.system.maxSafeTemperatureSensorVoltage * 2.0
        maxT = self.system.maxSafeTemperature * 2.0
        self.system.maxSafeTemperatureSensorVoltage = maxU
        self.system.maxSafeTemperature = maxT

        self.assertFalse(self.system._isUnsafe(maxU / 1.5, maxT / 1.5))
        self.assertFalse(self.system._isUnsafe(maxU, maxT / 1.5))
        self.assertFalse(self.system._isUnsafe(maxU / 1.5, maxT))
        self.assertFalse(self.system._isUnsafe(maxU, maxT))
        self.assertFalse(self.system._isUnsafe(maxU / 1.5, None))
        self.assertFalse(self.system._isUnsafe(maxU, None))

        self.assertTrue(self.system._isUnsafe(maxU * 1.5, maxT * 1.5))
        self.assertTrue(self.system._isUnsafe(maxU, maxT * 1.5))
        self.assertTrue(self.system._isUnsafe(maxU * 1.5, maxT))
        self.assertTrue(self.system._isUnsafe(maxU * 1.5, None))

        self.assertRaises(ValueError, self.system._isUnsafe, None, None)
        self.assertRaises(ValueError, self.system._isUnsafe, None, maxT)


    def testEnterSafeMode(self):
        """Tests the :meth:`enterSafeMode` method."""
        safeCurrent = self.system.heatingCurrentInSafeMode * 2
        self.system.heatingCurrentInSafeMode = safeCurrent
        self.system.startHeatingWithCurrent(safeCurrent * 2)
        logger = test.wrapLogger(self.system.startHeatingWithCurrent)
        self.system.lock(42)

        self.system.enterSafeMode()
        self.assertTrue(self.system.isInSafeMode)
        self.assertEqual(logger.log, [(safeCurrent, 42)])

        # Do not pointlessly call startHeatingWithCurrent.
        self.system.enterSafeMode()
        self.assertTrue(self.system.isInSafeMode)
        self.assertEqual(logger.log, [(safeCurrent, 42)])

        self.system.unlock(42)

        self.system.startHeatingWithCurrent(safeCurrent / 2)
        self.assertFalse(self.system.isInSafeMode)
        self.assertEqual(logger.log, [(safeCurrent, 42), safeCurrent / 2])

        # Do not pointlessly call startHeatingWithCurrent here either.
        self.system.enterSafeMode()
        self.assertTrue(self.system.isInSafeMode)
        self.assertEqual(logger.log, [(safeCurrent, 42), safeCurrent / 2])


    def testIsInSafeMode(self):
        """Tests the :attr:`isInSafeMode` property."""
        self.system.performMagicCalibration()
        safeCurrent = self.system.heatingCurrentInSafeMode
        maxTemperature = self.system.maxTargetTemperature

        self.assertFalse(self.system.isInSafeMode)

        for multiplier in (2.0, 2.0, 0.5, 1.0, 0.0, 3.0):
            self.system.startHeatingWithCurrent(safeCurrent * multiplier)
            self.assertFalse(self.system.isInSafeMode)
            self.system.enterSafeMode()
            self.assertTrue(self.system.isInSafeMode)

        for multiplier in (0.4, 0.4, 0.6, 0.8):
            self.system.startHeatingToTemperature(maxTemperature * multiplier)
            self.assertFalse(self.system.isInSafeMode)
            self.system.enterSafeMode()
            self.assertTrue(self.system.isInSafeMode)

        self.assertRaises(AttributeError,
            setattr, self.system, 'isInSafeMode', False)


    ###########################################################################
    # HEATING                                                                 #
    ###########################################################################

    def testHeatingCurrent(self):
        """Tests the :attr:`heatingCurrent` property."""
        for i in (2.0, 8.0, 0.0, 4.5):
            self.system.startHeatingWithCurrent(i)
            self.assertEqual(self.system.heatingCurrent, i)

        self.assertRaises(AttributeError,
            setattr, self.system, 'heatingCurrent', 3.0)


    def testTemperatureSensorVoltage(self):
        """Tests the :attr:`temperatureSensorVoltage` property."""
        voltages = [0.2, 0.8, 0.0, 0.45]
        self.system._interface = DeviceInterfaceStub(voltages=voltages)

        for u in voltages:
            self.assertEqual(self.system.temperatureSensorVoltage, u)

        self.assertRaises(AttributeError,
            setattr, self.system, 'temperatureSensorVoltage', 0.3)


    def testTemperature(self):
        """Tests the :attr:`temperature` property."""
        self.assertEqual(self.system.temperature, None)

        voltages = [0.2, 0.8, 0.0, 0.45]
        self.system._interface = DeviceInterfaceStub(voltages=voltages)
        self.system.calibrationData = test.makeCalibrationData()

        for u in voltages:
            self.assertAlmostEqual(self.system.temperature, u * 1000)

        self.assertRaises(AttributeError,
            setattr, self.system, 'temperature', 1200.0)


    def testTargetTemperature(self):
        """Tests the :attr:`targetTemperature` property."""
        self.assertEqual(self.system.targetTemperature, None)

        self.system.performMagicCalibration()

        self.assertEqual(self.system.targetTemperature, None)
        self.system.startHeatingToTemperature(700.0)
        self.assertEqual(self.system.targetTemperature, 700.0)
        self.system.startHeatingToTemperature(1200.0)
        self.assertEqual(self.system.targetTemperature, 1200.0)
        self.system.startHeatingWithCurrent(4.0)
        self.assertEqual(self.system.targetTemperature, None)
        self.system.startHeatingToTemperature(850.0)
        self.assertEqual(self.system.targetTemperature, 850.0)

        self.assertRaises(AttributeError,
            setattr, self.system, 'targetTemperature', 300.0)


    def testMinTargetTemperature(self):
        """Tests the :attr:`minTargetTemperature` property."""
        self.assertEqual(self.system.maxTargetTemperature, None)

        self.system.calibrationData = test.makeCalibrationData()

        # Do not exceed lowest calibration measurement.
        self.assertAlmostEqual(self.system.minTargetTemperature, 200.0)

        self.assertRaises(AttributeError,
            setattr, self.system, 'minTargetTemperature', 250.0)


    def testMaxTargetTemperature(self):
        """Tests the :attr:`maxTargetTemperature` property."""
        self.assertEqual(self.system.maxTargetTemperature, None)

        self.system.calibrationData = test.makeCalibrationData()

        # Do not exceed temperature with max heating current.
        self.system.maxHeatingCurrent = 10.0
        self.system.maxSafeTemperature = 5000.0
        self.assertAlmostEqual(self.system.maxTargetTemperature, 1000.0)

        # Do not exceed maxSafeTemperature.
        self.system.maxHeatingCurrent = 50.0
        self.system.maxSafeTemperature = 800.0
        self.assertEqual(self.system.maxTargetTemperature, 800.0)

        # Do not exceed greatest calibration measurement.
        self.system.maxHeatingCurrent = 50.0
        self.system.maxSafeTemperature = 5000.0
        self.assertEqual(self.system.maxTargetTemperature, 2000.0)

        self.assertRaises(AttributeError,
            setattr, self.system, 'maxTargetTemperature', 1500.0)


    def testMaxTargetTemperatureWithWonkyCalibrationData(self):
        """
        Tests that :meth:`maxTargetTemperature` returns a valid target value
        even in situations where wonky calibration data makes finding the
        correct value difficult.
        """
        cd = ops.calibration.data.CalibrationData()
        # Do not modify these values! They have been carefully picked to ensure
        # that an error would occur when calling startHeatingToTemperature with
        # a maxTargetTemperature calculated from them if the latter method
        # wouldn't ensure that the error won't occur.
        cd.addMeasurement( 2.0, 0.6,  438.0)
        cd.addMeasurement( 4.0, 0.9, 1287.0)
        cd.addMeasurement( 6.0, 1.0, 1290.0)
        cd.addMeasurement( 8.0, 4.0, 2376.0)
        cd.addMeasurement(10.0, 4.5, 2642.0)
        cd.addMeasurement(12.0, 4.8, 3189.0)
        cd.addMeasurement(14.0, 5.6, 3325.0)
        self.system.calibrationData = cd

        self.system.maxHeatingCurrent = maxI = 4.0
        self.system.maxSafeTemperature = 10000.0

        # Must not raise an InvalidHeatingCurrentErrror.
        self.system.startHeatingToTemperature(self.system.maxTargetTemperature)


    def testIsValidTargetTemperature(self):
        """Tests the :meth:`isValidTargetTemperature` method."""
        class SimplifiedProductionSystem(ProductionSystem):
            minTargetTemperature = 200.0
            maxTargetTemperature = 800.0

        self.mediator = gui.mediator.Mediator(logging=True)
        self.system = SimplifiedProductionSystem(self.mediator)

        method = self.system.isValidTargetTemperature

        self.assertRaises(NotCalibratedError, method, 100.0)
        self.assertRaises(NotCalibratedError, method, 900.0)

        self.system.performMagicCalibration()

        self.assertTrue(self.system.isValidTargetTemperature(500.0))
        self.assertTrue(self.system.isValidTargetTemperature(200.0))
        self.assertTrue(self.system.isValidTargetTemperature(800.0))
        self.assertFalse(self.system.isValidTargetTemperature(100.0))
        self.assertFalse(self.system.isValidTargetTemperature(900.0))


    def testIsValidTargetTemperatureErrors(self):
        """Tests the exceptions raised by :meth:`isValidTargetTemperature`."""
        self.assertRaises(NotCalibratedError,
            self.system.isValidTargetTemperature, 400.0)


    def testStartHeatingWithCurrent(self):
        """Tests the :meth:`startHeatingWithCurrent` method."""
        self.system.maxHeatingCurrent = 10.0
        self.system.lock(key=23)

        method = self.system.startHeatingWithCurrent

        method(6.0, key=23)
        self.assertEqual(self.system._interface.heatingCurrent, 6.0)
        method(8.0, key=23)
        self.assertEqual(self.system._interface.heatingCurrent, 8.0)
        method(0.0, key=23)
        self.assertEqual(self.system._interface.heatingCurrent, 0.0)

        self.system.unlock(key=23)

        method(5.0)
        self.assertEqual(self.system._interface.heatingCurrent, 5.0)


    def testStartHeatingWithCurrentErrors(self):
        """Tests the exceptions raised by :meth:`startHeatingWithCurrent`."""
        self.system.maxHeatingCurrent = 10.0

        method = self.system.startHeatingWithCurrent

        self.assertLocksAsExpected(method, 12.0)
        self.assertRaises(InvalidHeatingCurrentError, method, 12.0)
        self.assertRaises(InvalidHeatingCurrentError, method, -10.0)


    def testStartHeatingToTemperature(self):
        """Tests the :meth:`startHeatingToTemperature` method."""
        self.system.maxHeatingCurrent = 10.0
        self.system.isValidTargetTemperature = lambda t: True
        self.system.calibrationData = test.makeCalibrationData()
        self.system.lock(key=23)

        method = self.system.startHeatingToTemperature

        method(700.0, key=23)
        self.assertAlmostEqual(self.system.heatingCurrent, 7.0)
        method(900.0, key=23)
        self.assertAlmostEqual(self.system.heatingCurrent, 9.0)

        self.system.unlock(key=23)

        method(300.0)
        self.assertAlmostEqual(self.system.heatingCurrent, 3.0)


    def testStartHeatingToTemperatureErrors(self):
        """Tests the exceptions raised by :meth:`startHeatingToTemperature`."""
        self.system.isValidTargetTemperature = lambda t: False

        method = self.system.startHeatingToTemperature

        self.assertLocksAsExpected(method, 700.0)
        self.assertRaises(NotCalibratedError, method, 700.0)
        self.system.performMagicCalibration()
        self.assertRaises(InvalidTargetTemperatureError, method, 700.0)


    def testIdle(self):
        """Tests the :meth:`idle` method."""
        idleCurrent = self.system.heatingCurrentWhileIdle / 2
        self.system.heatingCurrentWhileIdle = idleCurrent
        self.system.startHeatingWithCurrent(idleCurrent * 4)
        self.system.lock(key=42)

        self.system.idle(key=42)
        self.assertEqual(self.system.heatingCurrent, idleCurrent)

        self.system.unlock(key=42)
        self.system.startHeatingWithCurrent(idleCurrent * 4)

        self.system.idle()
        self.assertEqual(self.system.heatingCurrent, idleCurrent)

        self.assertLocksAsExpected(self.system.idle)


    ###########################################################################
    # HEATER MOVEMENT                                                         #
    ###########################################################################

    def testHeaterPosition(self):
        """Tests the :attr:`heaterPosition` property."""
        positions = [0.4, 0.2, 1.0, 0.8, 0.0, 0.6]
        self.system._interface = DeviceInterfaceStub(positions=positions)

        for p in positions:
            self.assertEqual(self.system.heaterPosition, p)

        self.assertRaises(AttributeError,
            setattr, self.system, 'heaterPosition', 0.3)


    def testHeaterTargetPosition(self):
        """Tests the :attr:`heaterTargetPosition` property."""
        for position in (0.4, 0.2, 1.0, 0.8, 0.0, 0.6):
            self.system.startHeaterMovement(position)
            self.assertEqual(self.system.heaterTargetPosition, position)

        self.assertRaises(AttributeError,
            setattr, self.system, 'heaterTargetPosition', 0.3)


    def testStartHeaterMovement(self):
        """Tests the :meth:`startHeaterMovement` method."""
        self.system.lock(key=23)

        for p in (0.4, 0.2, 1.0, 0.8, 0.0, 0.6):
            self.system.startHeaterMovement(p, key=23)
            self.assertEqual(self.system._interface.heaterTargetPosition, p)

        self.system.unlock(key=23)


    def testStartHeaterMovementErrors(self):
        """Tests the exceptions raised by :meth:`startHeaterMovement`."""
        method = self.system.startHeaterMovement

        self.assertLocksAsExpected(method, 1.2)
        self.assertRaises(InvalidHeaterPositionError, method, 1.2)
        self.assertRaises(InvalidHeaterPositionError, method, -0.2)


    ###########################################################################
    # TESTING                                                                 #
    ###########################################################################

    def testIsSimulation(self):
        """Tests the :attr:`isSimulation` property."""
        for result in (True, False):
            self.system._interface = DeviceInterfaceStub(isSimulation=result)
            self.assertEqual(self.system.isSimulation, result)


    def testSpeedFactor(self):
        """Tests the :attr:`speedFactor` property."""
        self.system._interface.speedFactor = 5.0
        self.assertTrue(self.system.speedFactor, 5.0)

        self.system.speedFactor = 2.5
        self.assertTrue(self.system._interface.speedFactor, 2.5)

        self.system._interface = DeviceInterfaceStub(isSimulation=False)
        self.assertRaises(RequiresSimulationError,
            getattr, self.system, 'speedFactor')
        self.assertRaises(RequiresSimulationError,
            setattr, self.system, 'speedFactor', 1.0)


    def testPerformMagicCalibration(self):
        """Tests the :attr:`performMagicCalibration` method."""
        self.system.performMagicCalibration()
        self.assertTrue(self.system.isCalibrated)

        self.system._interface = DeviceInterfaceStub(isSimulation=False)
        self.assertRaises(
            RequiresSimulationError, self.system.performMagicCalibration)


    ###########################################################################
    # TEST UTILITY METHODS                                                    #
    ###########################################################################

    def assertLocksAsExpected(self, method, *parameters):
        """Asserts that `method` raises the expected locking-related errors."""
        if parameters:
            self.assertRaises(SystemNotLockedError, method, parameters, key=42)
            self.system.lock(key=42)
            self.assertRaises(SystemLockedError, method, parameters)
            self.assertRaises(WrongKeyError, method, parameters, key=23)
            self.system.unlock(key=42)
        else:
            self.assertRaises(SystemNotLockedError, method, key=42)
            self.system.lock(key=42)
            self.assertRaises(SystemLockedError, method)
            self.assertRaises(WrongKeyError, method, key=23)
            self.system.unlock(key=42)
