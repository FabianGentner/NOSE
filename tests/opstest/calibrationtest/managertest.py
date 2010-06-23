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

import math
import time
import unittest

from ops.calibration.manager import *
from ops.calibration.event import *
from test import *

import gui.mediator
import ops.interface
import ops.system
import util


class CalibrationManagerTests(unittest.TestCase):
    """
    Tests for the :class:`~ops.calibration.manager.CalibrationManager` class.
    """

    def setUp(self):
        self.mediator = gui.mediator.Mediator(logging=True)
        self.system = ops.system.ProductionSystem(self.mediator)
        self.cd = self.system.calibrationData

        uncleanCurrents = [4.0, 6.0, 12.0, 8.0, 10.0, 4.0, 8.0, 12.0, 6.0]
        self.currents = (4.0, 6.0, 8.0, 10.0, 12.0)

        self.manager = CalibrationManager(self.system, uncleanCurrents)
        self.manager.tickInterval = self.newTickInterval = 60000


    def tearDown(self):
        # Some tests modify :mod:`ops.calibration.manager`'s reference to the
        # :mod:`time` module in order to feed it canned timestamps. Fix that.
        ops.calibration.manager.time = time

        if hasattr(self.manager, '_leastSquareThread'):
            self.manager._leastSquareThread.stop()


    ###########################################################################
    # GENERAL ATTRIBUTES                                                      #
    ###########################################################################

    def testCurrentsCleanup(self):
        """
        Checks that the currents passed to :meth:`__init__` are sorted,
        and that duplicate entries are removed.
        """
        self.assertEqual(self.manager._currents, self.currents)


    def testReadOnly(self):
        """Checks that read-only properties are actually read-only."""
        properties = ('system currents isRunning state hasMoreHeatingStages '
            'heatingStageIndex heatingStageCount remainingHeatingStageCount')
        for p in properties.split():
            self.assertRaises(AttributeError, setattr, self.manager, p, None)


    def testSystem(self):
        """Checks that the :attr:`system` property is correctly set."""
        self.assertEqual(self.manager.system, self.system)


    def testCurrents(self):
        """Checks that the :attr:`currents` property is correctly set."""
        self.assertEqual(self.manager.currents, (4.0, 6.0, 8.0, 10.0, 12.0))


    def testIsRunning(self):
        """Tests the :attr:`isRunning` property."""
        self.assertFalse(self.manager.isRunning)
        self.manager.startCalibration()
        self.assertTrue(self.manager.isRunning)
        self.manager._startHeatingStage()
        self.assertTrue(self.manager.isRunning)
        self.manager._sendTemperatureRequest()
        self.assertTrue(self.manager.isRunning)
        self.manager.abortCalibration()
        self.assertFalse(self.manager.isRunning)


    def testState(self):
        """Tests the :attr:`state` property."""
        self.assertEqual(self.manager.state, STATE_NOT_YET_STARTED)
        self.manager.startCalibration()
        self.assertEqual(self.manager.state, STATE_MOVING_HEATER)
        self.manager._startHeatingStage()
        self.assertEqual(self.manager.state, STATE_HEATING)
        self.manager._sendTemperatureRequest()
        self.assertEqual(self.manager.state, STATE_WAITING_FOR_TEMPERATURE)
        self.manager.abortCalibration()
        self.assertEqual(self.manager.state, STATE_DONE)


    def testStartCalibration(self):
        """Tests the :meth:`startCalibration` method."""
        self.manager.startCalibration()

        self.assertTrue(self.system.isLocked)
        self.assertEqual(self.manager.state, STATE_MOVING_HEATER)

        timeout, callback = self.mediator.timeoutsAdded[-1]
        self.assertEqual(timeout, self.newTickInterval)
        self.assertTrue(callback.isSameMethod(self.manager._tick))

        event = self.mediator.eventsNoted[-1]
        self.assertEqual(event.system, self.system)
        self.assertEqual(event.manager, self.manager)


    def testStartCalibrationTwice(self):
        """Tests calling :meth:`startCalibration` twice."""
        self.manager.startCalibration()
        self.manager._startHeatingStage()
        eventsNoted = self.mediator.eventsNoted
        timeoutsAdded = self.mediator.timeoutsAdded

        self.assertRaises(util.ApplicationError, self.manager.startCalibration)

        # Nothing should have happened.
        self.assertEqual(self.manager.state, STATE_HEATING)
        self.assertEqual(self.mediator.eventsNoted, eventsNoted)
        self.assertEqual(self.mediator.timeoutsAdded, timeoutsAdded)


    def testStartCalibrationWithNoCurrents(self):
        """Tests :meth:`startCalibration` without currents."""
        moveLogger = wrapLogger(self.manager._startHeaterMovement)
        doneLogger = wrapLogger(self.manager._done)
        self.manager._currents = []

        self.manager.startCalibration()
        self.assertEqual(moveLogger.log, [])
        self.assertEqual(doneLogger.log, [STATUS_FINISHED])


    def testStartCalibrationWithNoLegalCurrents(self):
        """Tests :meth:`startCalibration` without legal currents."""
        moveLogger = wrapLogger(self.manager._startHeaterMovement)
        doneLogger = wrapLogger(self.manager._done)
        self.manager._currents = [1000.0]

        self.manager.startCalibration()
        self.assertEqual(moveLogger.log, [])
        self.assertEqual(doneLogger.log, [STATUS_INVALID_CURRENT])


    def testAbortCalibration(self):
        """Tests the :meth:`abortCalibration` method."""
        doneLogger = wrapLogger(self.manager._done)
        self.manager.startCalibration()
        self.manager.abortCalibration()
        self.assertEqual(doneLogger.log, [STATUS_ABORTED])


    def testAbortCalibrationTwice(self):
        """Tests calling :meth:`abortCalibration` twice."""
        doneLogger = wrapLogger(self.manager._done)
        self.manager.startCalibration()
        self.manager.abortCalibration()
        self.assertRaises(util.ApplicationError, self.manager.abortCalibration)
        self.assertEqual(doneLogger.log, [STATUS_ABORTED])


    def testAbortUnstartedCalibration(self):
        """Tests aborting a calibration procedure that hasn't been started."""
        doneLogger = wrapLogger(self.manager._done)
        self.assertRaises(util.ApplicationError, self.manager.abortCalibration)
        self.assertEqual(doneLogger.log, [])


    def testDone(self):
        """Tests the :meth:`_done` method."""
        self.manager.startCalibration()
        self.manager._state = 'dummy state'

        idleLogger = wrapLogger(self.system.idle)
        stageLogger = wrapLogger(
            self.manager._getNumberOfFinishedHeatingStages)

        self.manager._done('dummy status')

        self.assertEqual(self.manager.state, STATE_DONE)
        self.assertEqual(len(idleLogger.log), 1)
        self.assertFalse(self.system.isLocked)
        self.assertEqual(stageLogger.log, ['dummy status'])
        self.assertEqual(self.mediator.eventsNoted[-1], CalibrationOver(
            self.system, self.manager, 'dummy status',
            (), tuple(self.currents)))


    def testDoNotIdleIfDoneBecauseSafeModeWasTriggered(self):
        """
        Checks that :meth:`_done` does not have the production system idle
        if the safe mode has been triggered.
        """
        logger = wrapLogger(self.system.idle)
        self.manager.startCalibration()
        self.manager._state = 'dummy state'
        self.manager._done(STATUS_SAFE_MODE_TRIGGERED)
        self.assertEqual(logger.log, [])


    def testStopLeastSquareThreadIfDoneWhileHeating(self):
        """
        Checks that :meth:`_done` stops the least square thread if it is
        called in :data:`STATE_HEATING`.
        """
        self.manager.startCalibration()
        self.manager._state = STATE_HEATING
        self.manager._leastSquareThread = LeastSquareThread(None)
        self.manager._done('dummy status')
        self.assertTrue(self.manager._leastSquareThread._done)


    def testSendTemperatureRequestOverEventIfDoneWhileWaiting(self):
        """
        Checks that :meth:`_done` sends a TemperatureRequestOver event if
        it is called in :data:`STATE_WAITING_FOR_TEMPERATURE`.
        """
        logger = wrapLogger(self.manager._sendTemperatureRequestOverEvent)
        self.manager.startCalibration()
        self.manager._state = STATE_WAITING_FOR_TEMPERATURE
        self.manager._done('dummy status')
        self.assertEqual(logger.log, [()])


    # FIXME: Removed; write test for replacement method.
    #def testGetUnusedCurrents(self):
        #"""Tests the :meth:`_getUnusedCurrents` method."""
        #method = self.manager._getUnusedCurrents

        #statusValues = (STATUS_ABORTED, STATUS_SAFE_MODE_TRIGGERED,
            #STATUS_INVALID_CURRENT, STATUS_FINISHED)

        #for status in statusValues:
            #self.assertEqual(method(status), (4.0, 6.0, 8.0, 10.0, 12.0))

        #self.manager._heatingStageIndex = 2

        #self.assertEqual(method(STATUS_ABORTED), (8.0, 10.0, 12.0))
        #self.assertEqual(
            #method(STATUS_SAFE_MODE_TRIGGERED), (8.0, 10.0, 12.0))
        #self.assertEqual(method(STATUS_INVALID_CURRENT), (10.0, 12.0))
        #self.assertEqual(method(STATUS_FINISHED), (10.0, 12.0))


    ###########################################################################
    # TICK                                                                    #
    ###########################################################################

    # Use of :attr:`tickInterval` is tested in :meth:`testStartCalibration`.

    def testTickInSafeMode(self):
        """Tests :meth:`_tick` when the safe mode has been triggered."""
        doneLogger = wrapLogger(self.manager._done)
        self.manager.startCalibration()
        self.manager._state = 'dummy state'
        self.system.enterSafeMode()

        self.assertFalse(self.manager._tick())
        self.assertEqual(doneLogger.log, [STATUS_SAFE_MODE_TRIGGERED])


    def testTickWhileMovingHeater(self):
        """Tests :meth:`_tick` in :data:`STATE_MOVING_HEATER`."""
        logger = replaceWithLogger(self.manager._checkHeaterPosition)
        self.manager.startCalibration()

        self.assertTrue(self.manager._tick())
        self.assertEqual(logger.log, [()])


    def testTickWhileHeating(self):
        """Tests :meth:`_tick` in :data:`STATE_HEATING`."""
        logger = replaceWithLogger(self.manager._checkHeatingProgress)
        self.manager.startCalibration()
        self.manager._startHeatingStage()

        self.assertTrue(self.manager._tick())
        self.assertEqual(logger.log, [()])


    def testTickWhileWatingForTemperature(self):
        """Tests :meth:`_tick` in :data:`STATE_WAITING_FOR_TEMPERATURE`."""
        self.manager._state = STATE_WAITING_FOR_TEMPERATURE
        self.assertTrue(self.manager._tick())


    def testTickWhenDone(self):
        """Tests :meth:`_tick` in :data:`STATE_DONE`."""
        self.manager._state = STATE_DONE
        self.assertFalse(self.manager._tick())


    ###########################################################################
    # HEATER MOVEMENT                                                         #
    ###########################################################################

    def testStartHeaterMovement(self):
        """Tests the :meth:`_startHeaterMovement` method."""
        self.manager.startCalibration()
        self.system._interface._heaterStartingPosition = 0.3
        self.system._interface._heaterTargetPosition = 0.3

        self.manager._startHeaterMovement()
        self.assertTrue(self.manager.state, STATE_MOVING_HEATER)
        self.assertEqual(self.manager._initialHeaterPosition, 0.3)
        self.assertEqual(self.system.heaterTargetPosition, 1.0)


    def testCheckHeaterPosition(self):
        """Tests the :meth:`_checkHeaterPosition` method."""
        logger = replaceWithLogger(self.manager._startHeatingStage)
        self.manager._system = Stub(ops.system.ProductionSystem,
            heaterPosition=queue(0.0, 0.5, 1.0))

        self.manager._checkHeaterPosition()
        self.assertEqual(logger.log, [])
        self.manager._checkHeaterPosition()
        self.assertEqual(logger.log, [])
        self.manager._checkHeaterPosition()
        self.assertEqual(logger.log, [()])


    ###########################################################################
    # HEATING                                                                 #
    ###########################################################################

    def testHasMoreHeatingStages(self):
        """Tests the :attr:`hasMoreHeatingStages` property."""
        self.manager._currents = []
        self.assertFalse(self.manager.hasMoreHeatingStages)

        self.manager._currents = [10000.0]
        self.assertFalse(self.manager.hasMoreHeatingStages)

        self.manager._currents = [4.0, 6.0, 8.0]
        self.assertTrue(self.manager.hasMoreHeatingStages)
        self.manager._heatingStageIndex = 0
        self.assertTrue(self.manager.hasMoreHeatingStages)
        self.manager._heatingStageIndex = 1
        self.assertTrue(self.manager.hasMoreHeatingStages)
        self.manager._heatingStageIndex = 2
        self.assertFalse(self.manager.hasMoreHeatingStages)

        self.manager._currents = [4.0, 6.0, 8.0, 1000.0]
        self.assertFalse(self.manager.hasMoreHeatingStages)

        self.manager._currents = [4.0, 6.0, 8.0, 10.0]
        self.assertTrue(self.manager.hasMoreHeatingStages)


    def testExplainNoMoreHeatingStages(self):
        """Tests the :meth:`_explainNoMoreHeatingStages` method."""
        method = self.manager._explainNoMoreHeatingStages

        self.manager._currents = []
        self.assertEqual(method(), STATUS_FINISHED)

        self.manager._currents = [1000.0]
        self.assertEqual(method(), STATUS_INVALID_CURRENT)

        self.manager._currents = [4.0, 6.0, 8.0]
        self.manager._heatingStageIndex = 2
        self.assertEqual(method(), STATUS_FINISHED)

        self.manager._currents = [4.0, 6.0, 8.0, 1000.0]
        self.assertEqual(method(), STATUS_INVALID_CURRENT)


    def testHeatingStageIndex(self):
        """Tests the :attr:`heatingStageIndex` property."""
        # _startLeastSquareThread, which is called from _startHeatingStage,
        # doesn't like being called again before the thread started in the
        # previous heating stage comes up with a solution.
        replaceWithLogger(self.manager._startLeastSquareThread)

        self.manager.startCalibration()
        self.assertEqual(self.manager.heatingStageIndex, -1)
        self.manager._startHeatingStage()
        self.assertEqual(self.manager.heatingStageIndex, 0)
        self.manager._startHeatingStage(300)
        self.assertEqual(self.manager.heatingStageIndex, 1)
        self.manager._startHeatingStage(600)
        self.assertEqual(self.manager.heatingStageIndex, 2)


    def testHeatingStageCount(self):
        """Tests the :attr:`heatingStageCount` property."""
        self.manager._currents = [4.0, 6.0, 8.0, 10.0, 12.0]
        self.assertEqual(self.manager.heatingStageCount, 5)
        self.manager._heatingStageIndex = 2   # shouldn't make a difference
        self.assertEqual(self.manager.heatingStageCount, 5)
        self.manager._currents = [4.0, 6.0, 8.0]
        self.assertEqual(self.manager.heatingStageCount, 3)
        self.manager._currents = [4.0, 6.0, 8.0, 10.0, 1000.0]
        self.assertEqual(self.manager.heatingStageCount, 4)


    def testRemainingHeatingStageCount(self):
        """Tests the :attr:`remainingHeatingStageCount` property."""
        self.manager._currents = [4.0, 6.0, 8.0, 10.0, 12.0]
        self.assertEqual(self.manager.remainingHeatingStageCount, 5)
        self.manager._heatingStageIndex = 3
        self.assertEqual(self.manager.remainingHeatingStageCount, 1)
        self.manager._heatingStageIndex = 4
        self.assertEqual(self.manager.remainingHeatingStageCount, 0)
        self.manager._heatingStageIndex = 10
        self.assertEqual(self.manager.remainingHeatingStageCount, 0)
        self.manager._currents = [0.4, 0.6, 0.8, 1000.0, 2000.0, 3000.0]
        self.manager._heatingStageIndex = -1
        self.assertEqual(self.manager.remainingHeatingStageCount, 3)
        self.manager._heatingStageIndex = 1
        self.assertEqual(self.manager.remainingHeatingStageCount, 1)
        self.manager._heatingStageIndex = 2
        self.assertEqual(self.manager.remainingHeatingStageCount, 0)
        self.manager._heatingStageIndex = 3
        self.assertEqual(self.manager.remainingHeatingStageCount, 0)


    def testStartFirstHeatingStage(self):
        """Tests calling :meth:`_startHeatingStage` for the first time."""
        logger = wrapLogger(self.manager._startLeastSquareThread)
        ops.calibration.manager.time = Stub(time, time=fun(once(23.0)))
        self.manager.startCalibration()

        self.manager._startHeatingStage()
        self.assertEqual(self.manager.state, STATE_HEATING)
        self.assertEqual(self.manager.heatingStageIndex, 0)
        self.assertEqual(self.manager._stageStartingTime, 23.0)
        self.assertEqual(self.manager._totalPreviousStageTime, 0.0)
        self.assertEqual(self.manager._times, [])
        self.assertEqual(self.manager._voltages, [])
        self.assertEqual(logger.log, [None])
        self.assertEqual(self.system.heatingCurrent, self.currents[0])


    def testStartSubsequentHeatingStage(self):
        """Tests calls to :meth:`_startHeatingStage` other than the first."""
        logger = replaceWithLogger(self.manager._startLeastSquareThread)
        ops.calibration.manager.time = Stub(time, time=fun(once(42.0)))
        self.manager.startCalibration()

        # Pretend there have been previous heating stages.
        self.manager._heatingStageIndex = 3
        self.manager._totalPreviousStageTime = 'dummy'
        self.manager._times = self.manager._voltages = range(100)

        # Actual tests start here.
        self.manager._startHeatingStage(450.0)
        self.assertEqual(self.manager.state, STATE_HEATING)
        self.assertEqual(self.manager.heatingStageIndex, 4)
        self.assertEqual(self.manager._stageStartingTime, 42.0)
        self.assertEqual(self.manager._totalPreviousStageTime, 'dummy')
        self.assertEqual(self.manager._times, [])
        self.assertEqual(self.manager._voltages, [])
        self.assertEqual(logger.log, [450.0])
        self.assertEqual(self.system.heatingCurrent, self.currents[4])


    def checkHeatingStageIndexWhenLeastSquareThreadIsStarted(self):
        """
        Cheks that :meth:`_startHeatingStage` increments the heatin stage index
        before it calls :meth:`_startLeastSquareThread`.
        """
        self.manager._startLeastSquareThread = None
        self.assertRaises(AttributeError, self.manager._startHeatingStage)
        self.assertEqual(self.manager.heatingStageIndex, 0)
        self.assertRaises(AttributeError, self.manager._startHeatingStage, 9.0)
        self.assertEqual(self.manager.heatingStageIndex, 1)


    def testStartFirstLeastSquareThread(self):
        """Tests calling :meth:`_startLeastSquareThread` for the first time."""
        self.manager._heatingStageIndex = 0
        self.manager._startLeastSquareThread()

        self.assertTrue(self.manager._leastSquareThread.isAlive)
        self.assertEqual(
            self.manager._leastSquareThread._startingEstimates,
            getFirstStartingEstimates(self.currents[0]))


    def testStartSubsequentLeastSquareThread(self):
        """
        Tests calling :meth:`_startLeastSquareThread` with starting estimates
        that reflect the results from the preceding heating stage.
        """
        lst = LeastSquareThread(None)
        lst._solution = Solution(500.0, 750.0, 35.0, tuple('dummy'))
        self.manager._leastSquareThread = lst
        self.manager._heatingStageIndex = 3
        self.manager._currents = (4.0, 6.0, 8.0, 10.5)

        # Actual tests start here.
        self.manager._startLeastSquareThread(678.0)
        self.assertNotEqual(self.manager._leastSquareThread, lst)
        self.assertTrue(self.manager._leastSquareThread.isAlive)
        self.assertEqual(
            self.manager._leastSquareThread._startingEstimates,
            getSubsequentStartingEstimates(678.0, lst.solution, 2.5))


    def testCheckHeatingProgressNotDone(self):
        """Tests :meth:`_checkHeatingProgress` before the stage is finished."""
        times = [10.1, 10.2, 10.3, 10.4, 10.5]
        heatingTimes = [t - 10.0 for t in times]
        voltages = [0.45, 0.5, 0.55, 0.6, 0.65]
        ops.calibration.manager.time = Stub(time, time=fun(queue(10., *times)))

        self.manager.startCalibration()
        self.manager._startHeatingStage()

        self.system._interface = Stub(
            ops.interface.DeviceInterface,
            heaterPosition=once(0.0),
            temperatureSensorVoltage=queue(*voltages))

        lst = self.manager._leastSquareThread
        logger = replaceWithLogger(lst.refreshData)

        # Actual tests start here.
        for n, (t, u) in enumerate(zip(times, voltages), start=1):
            self.manager._checkHeatingProgress()
            self.assertEqual(self.manager._times[-1], t - 10.0)
            self.assertEqual(self.manager._voltages[-1], u)
            self.assertEqual(logger.log[0]['times'], heatingTimes[:n])
            self.assertEqual(logger.log[0]['voltages'], voltages[:n])


    def testCheckHeatingProgressDone(self):
        """Tests :meth:`_checkHeatingProgress` when the stage is finished."""
        replaceWithLogger(self.manager.getProgress, [1.0])
        ops.calibration.manager.time = Stub(time, time=fun(queue(10.0, 52.0)))

        self.manager.startCalibration()
        self.manager._startHeatingStage()
        self.manager._totalPreviousStageTime += 23.0

        # Actual tests start here.
        self.manager._checkHeatingProgress()
        self.assertEqual(self.manager._totalPreviousStageTime, 65.0)
        self.assertTrue(self.manager._leastSquareThread._done)
        self.assertEqual(self.manager.state, STATE_WAITING_FOR_TEMPERATURE)


    ###########################################################################
    # PROGRESS ESTIMATION                                                     #
    ###########################################################################

    # Use of :attr:`precision` is tested in :meth:`testGetHeatingProgress`.

    def testGetProgressInStateMovingHeater(self):
        """Tests :meth:`getProgress` in :data:`STATE_MOVING_HEATER`."""
        l = replaceWithLogger(self.manager._getHeaterMovementProgress, [0.123])
        self.system._interface = Stub(ops.interface.DeviceInterface,
            heaterPosition=queue(0.23, 0.42), startHeaterMovement=fun(None))

        self.manager.startCalibration()

        self.assertEqual(self.manager.getProgress(), 0.123)
        self.assertEqual(l.log, [(0.42, 0.23)])


    def testGetProgressInStateHeating(self):
        """Tests :meth:`getProgress` in :data:`STATE_HEATING`."""
        l = replaceWithLogger(self.manager._getHeatingProgress, [0.23])

        self.manager.startCalibration()
        self.manager._startHeatingStage()

        # LeastSquareThread hasn't yet found a solution.
        self.assertEqual(self.manager.getProgress(), 0.0)

        # Pretend LeastSquareThread has been working for a while.
        self.manager._leastSquareThread._solution = Solution(*'fake')
        self.manager._times.append(0.42)

        self.assertEqual(self.manager.getProgress(), 0.23)
        self.assertEqual(l.log, [('f', 'a', 'k', 0.42)])


    def testGetProgressInOtherStates(self):
        """Tests :meth:`getProgress` in the other states."""
        self.manager._state = STATE_NOT_YET_STARTED
        self.assertEqual(self.manager.getProgress(), 0.0)
        self.manager._state = STATE_WAITING_FOR_TEMPERATURE
        self.assertEqual(self.manager.getProgress(), 1.0)
        self.manager._state = STATE_DONE
        self.assertEqual(self.manager.getProgress(), 1.0)


    def testGetHeaterMovementProgress(self):
        """Tests the :meth:`_getHeaterMovementProgress` method."""
        method = self.manager._getHeaterMovementProgress
        tests = ((0.2, 0.0), (0.4, 0.25), (0.6, 0.5), (0.8, 0.75))
        for position, expected in tests:
            self.assertAlmostEqual(method(position, 0.2), expected)
        self.assertEqual(method(0.2, 1.0), 1.0)
        self.assertEqual(method(1.0, 1.0), 1.0)


    def testGetHeatingProgress(self):
        """Tests the :meth:`_getHeatingProgress` method."""
        self.manager.precision = 10.0
        method = self.manager._getHeatingProgress
        expected = 10.0 / (35.0 * -math.log(1 - 40.0 / 50.0))
        self.assertEqual(method(75.0, 125.0, 35.0, 10.0), expected)
        self.assertEqual(method(125.0, 75.0, 35.0, 10.0), expected)
        self.assertEqual(method(125.0, 125.0, 35.0, 10.0), 1.0)
        self.assertEqual(method(75.0, 125.0, 35.0, 1000.0), 1.0)


    def testGetExtendedProgressInStateMovingHeater(self):
        """
        Tests :meth:`getExtendedProgress` in :data:`STATE_MOVING_HEATER`.
        """
        logger = replaceWithLogger(self.manager.getProgress, [0.23])
        self.manager.startCalibration()
        est = self.manager.getExtendedProgress()
        self.assertEqual(est.stageProgress, 0.23)
        self.assertEqual(est.stageTimeLeft, None)
        self.assertEqual(est.totalProgress, 0.0)
        self.assertEqual(est.totalTimeLeft, None)


    def testGetExtendedProgressInStateHeatingAndWaitingForTemperature(self):
        """
        Tests :meth:`getExtendedProgress` in :data:`STATE_HEATING` and
        :data:`STATE_WAITING_FOR_TEMPERATURE`.
        """
        replaceWithLogger(self.manager.getProgress, [0.23] * 2)
        gehpLogger = replaceWithLogger(
            self.manager._getExtendedHeatingProgress, ['dummy'] * 2)

        self.manager.startCalibration()
        self.manager._startHeatingStage()

        # Pretend there has been some previous activity.
        self.manager._heatingStageIndex += 2
        self.manager._times.append(0.42)
        self.manager._totalPreviousStageTime += 100.0

        # Actual tests starts here.
        est = self.manager.getExtendedProgress()
        self.assertEqual(est, 'dummy')
        self.assertEqual(gehpLogger.log, [(0.23, 2, 5, 0.42, 100.42)])

        self.manager._sendTemperatureRequest()

        est = self.manager.getExtendedProgress()
        self.assertEqual(est, 'dummy')
        self.assertEqual(gehpLogger.log, [(0.23, 2, 5, 0.42, 100.42)] * 2)


    def testGetExtendedProgressInOtherStates(self):
        """
        Tests :meth:`getExtendedProgress` in :data:`STATE_NOT_YET_STARTED`
        and :data:`STATE_DONE`.
        """
        est = self.manager.getExtendedProgress()
        self.assertEqual(est.stageProgress, 0.0)
        self.assertEqual(est.stageTimeLeft, None)
        self.assertEqual(est.totalProgress, 0.0)
        self.assertEqual(est.totalTimeLeft, None)

        self.manager.startCalibration()
        self.manager.abortCalibration()

        est = self.manager.getExtendedProgress()
        self.assertEqual(est.stageProgress, 1.0)
        self.assertEqual(est.stageTimeLeft, None)
        self.assertEqual(est.totalProgress, 1.0)
        self.assertEqual(est.totalTimeLeft, None)


    def testGetExtendedHeatingProgress(self):
        """Tests the :meth:`_getExtendedHeatingProgress` method."""
        x1 = 85.0 / (85.0 + 65.0)
        x2 = 90.0 / (90.0 + 60.0)
        x3 = 210.0 / (210.0 + 15.0)

        tests = (
            ((0.0, 0, 2,  1.0,   1.0), (0.0, None, 0.0, None)),
            ((0.1, 0, 2,  5.0,   5.0), (0.1, 45.0, 0.05, 95.0)),
            ((1.0, 0, 2, 25.0,  25.0), (1.0,  0.0, 0.5,  25.0)),

            ((0.0, 2, 5,  0.0,  80.0), (0.0, 40.0, 0.4, 120.0)),
            ((0.5, 2, 5,  5.0,  85.0), (0.5,  5.0, x1,   65.0)),
            ((1.0, 2, 5, 10.0,  90.0), (1.0,  0.0, x2,   60.0)),

            ((0.0, 3, 4,  0.0, 150.0), (0.0, 50.0, 0.75, 50.0)),
            ((0.8, 3, 4, 60.0, 210.0), (0.8, 15.0, x3,   15.0)),
            ((1.0, 3, 4, 80.0, 230.0), (1.0,  0.0, 1.0,   0.0)),

            ((0.0, 0, 1,  0.1,   0.1), (0.0, None, 0.0, None)),
            ((0.4, 0, 1, 10.0,  10.0), (0.4, 15.0, 0.4, 15.0)),
            ((1.0, 0, 1, 20.0,  20.0), (1.0,  0.0, 1.0,  0.0)))

        for params, expected in tests:
            est = self.manager._getExtendedHeatingProgress(*params)
            self.assertEqual(est.stageProgress, expected[0])
            self.assertEqual(est.stageTimeLeft, expected[1])
            self.assertEqual(est.totalProgress, expected[2])
            self.assertEqual(est.totalTimeLeft, expected[3])


    ###########################################################################
    # REQUESTING TEMPERATURES                                                 #
    ###########################################################################

    def testSendTemperatureRequest(self):
        """Tests the :meth:`_sendTemperatureRequest` method."""
        self.manager.startCalibration()
        self.manager._sendTemperatureRequest()
        self.assertEqual(self.manager.state, STATE_WAITING_FOR_TEMPERATURE)
        self.assertEqual(self.mediator.eventsNoted[-1], TemperatureRequested(
                self.manager,
                self.system,
                self.manager._temperatureReportCallback))


    def testNonfinalTemperatureReportCallbackCall(self):
        """
        Tests the :meth:`_temperatureReportCallback` method when there are
        still heating stages left.
        """
        self.manager.startCalibration()
        self.manager._startHeatingStage()
        self.manager._sendTemperatureRequest()

        logger = replaceWithLogger(self.manager._startHeatingStage)
        self.system._interface = Stub(ops.interface.DeviceInterface,
            heatingCurrent=once(4.0), temperatureSensorVoltage=once(0.23))

        # Actual tests start here.
        self.manager._temperatureReportCallback(42.0)
        expectedEvent = TemperatureRequestOver(self.manager, self.system)
        self.assertEqual(self.mediator.eventsNoted[-1], expectedEvent)
        self.assertEqual(self.cd.measurements, ((4.0, 0.23, 42.0),))
        self.assertEqual(logger.log, [42.0])


    def testFinalTemperatureReportCallbackCall(self):
        """
        Tests the :meth:`_temperatureReportCallback` method when there are
        no more heating stages left.
        """
        self.manager.startCalibration()
        self.manager._startHeatingStage()
        self.manager._sendTemperatureRequest()
        self.manager._heatingStageIndex = len(self.currents) - 1

        logger = replaceWithLogger(self.manager._done)
        replaceWithLogger(self.manager._explainNoMoreHeatingStages, ['dummy'])

        # Actual tests start here.
        self.manager._temperatureReportCallback(42.0)
        self.assertEqual(len(self.cd.measurements), 1)
        self.assertEqual(logger.log, ['dummy'])


    def testUnwantedTemperatureReportCallbackCall(self):
        """
        Tests calling the :meth:`_temperatureReportCallback` method when it's
        not supposed to be called.
        """
        method = self.manager._temperatureReportCallback
        self.assertRaises(util.ApplicationError, method, 300.0)
        for state in (STATE_MOVING_HEATER, STATE_HEATING, STATE_DONE):
            self.manager._state = state
            self.assertRaises(util.ApplicationError, method, 300.0)

