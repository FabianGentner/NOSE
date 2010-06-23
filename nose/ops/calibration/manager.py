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
This module contains the :class:`CalibrationManager` class, which is
responsible for :term:`calibrating <calibration>` the production system.

To start the calibration procedure, it is sufficient to create a calibration
manager instance and call its :meth:`~CalibrationManager.startCalibration`
method. The :class:`~ops.system.ProductionSystem` that is to be calibrated
and a list of :term:`heating currents <heating current>` that are to be used
are passed to the constructor.

The calibration manager sends a
:class:`~ops.calibration.event.CalibrationStarted` event when the procedure is
started, and a :class:`~ops.calibration.event.CalibrationOver` event when it
terminates. The production system is locked for the duration of the procedure.

The calibration procedure itself consists of a number of *calibration stages*.
During the first stage, the system's :term:`heater` is moved to its foremost
position. Subsequent stages are *heating stages*, which each use one of the
heating currents that are passed to the calibration manager's constructor.
At the end of each heating stage, when the temperature sensor voltage has
become reasonably stable, the user needs to take a :term:`temperature
measurement`. When a measurement is needed, the calibration manager sends a
:class:`~ops.calibration.event.TemperatureRequested` event.

The client is responsible for ensuring that some GUI component (most likely
a :class:`~gui.calibration.entry.TemperatureEntryHandler`) is listening for
these events, asks the user to take a measurement, and reports the result using
the callback function that is sent along with the event. When a measurement has
been reported, a :class:`~ops.calibration.event.TemperatureRequestOver` event
is sent.

The data that is collected during calibration is automatically added to the
:class:`~ops.calibration.data.CalibrationData` object of the production
system that is being calibrated. If the object already has data for a
given heating current, they are replaced with the new data gathered for that
current, but data for heating currents that are not used during the ongoing
calibration are retained, so that the calibration of a system can be refined
with subsequent calibration procedures.

The calibration data object uses the data to fit a number of *estimation
functions*, which are used to estimate the :term:`heating temperature`
that corresponds to a given :term:`temperature sensor voltage`, and the
heating current that results in the heating temperature reaching, but not
exceeding, a given *target temperature*. About twelve heating currents should
be used during calibration so that these functions can be properly fitted.

If a reasonable number of heating stages are used, the calibration procedure
may take several hours. The calibration manager provides a number of methods
(most notably :meth:`~CalibrationManager.getExtendedProgress`) that estimate
the procedure's progress and remaining duration, so that the user can receive
some feedback about the state of the procure while it is running. The classes
in the :mod:`gui.calibration.progress` module can be used to present this
information to the user.

The calibration procedure may end prematurely if it is aborted by a client,
or if the production system's :term:`safe mode` is triggered. The data that
have already been collected are used nevertheless.
"""

# NOTE: Some of this information is duplicated in the glossary.

import collections
import math
import time

from ops.calibration.leastsquare import *
from ops.calibration.event import *

import util


###############################################################################
# THE CALIBRATION MANAGER CLASS                                               #
###############################################################################

class CalibrationManager(object):
    """
    Creates a new instance of this class, using the arguments to set
    :attr:`system` and :attr:`currents`. `currents` is sorted first, and
    duplicate heating currents are removed.

    Heating currents in `currents` that exceed the :attr:`system`'s
    :attr:`~ops.system.ProductionSystem.maxHeatingCurrent` are skipped
    during calibration. In that case, the calibration procedure's exit
    status will be :data:`STATUS_INVALID_CURRENT`.
    """

    def __init__(self, system, currents):
        self._system = system

        # Currents that exceed maxHeatingCurrent are kept just in case that
        # maxHeatingCurrent is increased during the calibration procedure.
        self._currents = tuple(sorted(set(currents)))

        self._state = STATE_NOT_YET_STARTED
        self._heatingStageIndex = -1


    @property
    def system(self):
        """
        The :class:`~ops.system.ProductionSystem` that is being calibrated.
        Immutable.
        """
        return self._system


    @property
    def currents(self):
        """
        A sorted tuple of the heating currents for which measurements are to
        be taken, in mA. Immutable.
        """
        return self._currents


    @property
    def isRunning(self):
        """
        Indicates whether the calibration procedure is running. It starts
        running as soon as :meth:`startCalibration` is called, and terminates
        when a client calls :meth:`abortCalibration`, the production system's
        :term:`safe mode` is triggered, or a :term:`temperature measurement`
        for the last valid heating current is reported. Read-only.
        """
        return self.state not in (STATE_NOT_YET_STARTED, STATE_DONE)


    @property
    def state(self):
        """
        The state the calibration procedure is in. Must be one of
        :data:`STATE_NOT_YET_STARTED`, :data:`STATE_MOVING_HEATER`,
        :data:`STATE_HEATING`, :data:`STATE_WAITING_FOR_TEMPERATURE`,
        and :data:`STATE_DONE`. Read-only.
        """
        return self._state


    def startCalibration(self):
        """
        Starts the calibration procedure. Instances cannot be reused for a
        second calibration procedure, so this method may only be called once
        on any given object.
        """
        if self.state != STATE_NOT_YET_STARTED:
            message = 'the calibration procedure has already been started'
            raise util.ApplicationError(message)

        self.system.lock(key=self)
        self.system.mediator.noteEvent(CalibrationStarted(self.system, self))
        self.system.mediator.addTimeout(self.tickInterval, self._tick)

        if self.hasMoreHeatingStages:
            self._startHeaterMovement()
        else:
            self._done(self._explainNoMoreHeatingStages())


    def abortCalibration(self):
        """
        Aborts the calibration procedure. The data that have already been
        collected are still used.
        """
        if self.isRunning:
            self._done(STATUS_ABORTED)
        else:
            message = 'the calibration procedure is not running'
            raise util.ApplicationError(message)


    def _done(self, status):
        """
        Does some necessary chores after the heating process has been
        completed.
        """
        if self.state == STATE_HEATING:
            self._leastSquareThread.stop()

        if self.state == STATE_WAITING_FOR_TEMPERATURE:
            self._sendTemperatureRequestOverEvent()

        self._state = STATE_DONE

        if status != STATUS_SAFE_MODE_TRIGGERED:
            self.system.idle(key=self)

        self.system.unlock(key=self)

        stagesFinished = self._getNumberOfFinishedHeatingStages(status)
        usedCurrents = self.currents[:stagesFinished]
        unusedCurrents = self.currents[stagesFinished:]

        self.system.mediator.noteEvent(CalibrationOver(
            self.system, self, status, usedCurrents, unusedCurrents))


    def _getNumberOfFinishedHeatingStages(self, status):
        # TODO: Comment
        if status in (STATUS_INVALID_CURRENT, STATUS_FINISHED):
            # the heating stage with index heatingStageIndex has been finished,
            # or no heating stage has ever been started
            return self.heatingStageIndex + 1
        else:
            # the heating stage with index heatingStageIndex has been aborted,
            # or no heating stage has ever been started
            return max(0, self.heatingStageIndex)


    ###########################################################################
    # TICK                                                                    #
    ###########################################################################

    #: The interval in which the instance records temperature sensor voltages,
    #: in milliseconds. This is a class attribute, but it can be set on an
    #: instance before :meth:`startCalibration` is called to override the
    #: default value.
    tickInterval = 250


    def _tick(self):
        """
        If :attr:`system` has switched to its safe mode, this method
        terminates the calibration procedure. Otherwise, calls the
        *tick method* associated with the current state, if any.

        Called periodically by the :attr:`system`'s
        :attr:`~ops.system.ProductionSystem.mediator`.
        """
        if self.system.isInSafeMode:
            self._done(STATUS_SAFE_MODE_TRIGGERED)
        elif self.state == STATE_MOVING_HEATER:
            self._checkHeaterPosition()
        elif self.state == STATE_HEATING:
            self._checkHeatingProgress()

        # If this method returns True, it will be called again.
        return self.state != STATE_DONE


    ###########################################################################
    # HEATER MOVEMENT                                                         #
    ###########################################################################

    def _startHeaterMovement(self):
        """
        Issues a command to move the system's heater into its foremost
        position. This is necessary to receive accurate measurements from
        the temperature sensor and is an asynchronous operation whose progress
        is periodically checked by :meth:`_checkHeaterPosition`.
        """
        self._state = STATE_MOVING_HEATER
        self._initialHeaterPosition = self.system.heaterPosition
        self.system.startHeaterMovement(1.0, key=self)


    def _checkHeaterPosition(self):
        """
        A *tick method* that checks whether the heater has reached its
        foremost position and proceeds with the next part of the calibration
        procedure if it has.
        """
        if self.system.heaterPosition == 1.0:
            self._startHeatingStage()


    ###########################################################################
    # HEATING                                                                 #
    ###########################################################################

    @property
    def hasMoreHeatingStages(self):
        """
        Indicates whether there will be another heating stage after the
        current one (if any) is finished. This will be ``False`` if all
        heating currents in :attr:`currents` have been used, or if the
        next current in :attr:`currents` exceeds the :attr:`system`'s
        :attr:`~ops.system.ProductionSystem.maxHeatingCurrent`. Read-only.
        """
        nextIndex = self.heatingStageIndex + 1

        if nextIndex == len(self.currents):
            return False
        if self.currents[nextIndex] > self.system.maxHeatingCurrent:
            return False

        return True


    @property
    def heatingStageIndex(self):
        """
        The index of the ongoing heating stage, or ``-1`` if the procedure
        hasn't yet reached the first heating stage. In heating stage *n*,
        the heating current :samp:`currents[{n}]` is used. Read-only.
        """
        return self._heatingStageIndex


    def _explainNoMoreHeatingStages(self):
        """
        Can be called when there are no valid heating currents remaining to
        retrieve the status code that explains why the calibration procedure
        is over: either :data:`STATUS_FINISHED` if all currents have been used,
        or :data:`STATUS_INVALID_CURRENT` if the next current is invalid.
        """
        assert not self.hasMoreHeatingStages
        if self.heatingStageIndex + 1 == len(self.currents):
            return STATUS_FINISHED
        else:
            return STATUS_INVALID_CURRENT


    @property
    def heatingStageCount(self):
        """
        The number of heating stages the calibration procedure will have if
        it isn't terminated prematurely. May be less than ``len(currents)``,
        since some currents in :attr:`currents` may exceed the :attr:`system`'s
        :attr:`~ops.system.ProductionSystem.maxHeatingCurrent`. Read-only.
        """
        return self.remainingHeatingStageCount + self.heatingStageIndex + 1


    @property
    def remainingHeatingStageCount(self):
        """
        The number of heating stages left after the ongoing one (if any) is
        finished. May be less than ``len(currents) - heatingStageIndex - 1``,
        since some currents in :attr:`currents` may exceed the :attr:`system`'s
        :attr:`~ops.system.ProductionSystem.maxHeatingCurrent`. Read-only.
        """
        count = 0
        for current in self.currents[self.heatingStageIndex + 1:]:
            if current <= self.system.maxHeatingCurrent:
                count += 1
            else:
                break
        return count


    def _startHeatingStage(self, previousTemperature=None):
        """
        Starts heating with the next heating current in :attr:`currents`.
        `previousTemperature` is the heating temperature measured in the
        previous heating stage, if any.
        """
        assert self.hasMoreHeatingStages

        self._state = STATE_HEATING
        self._heatingStageIndex += 1
        self._stageStartingTime = time.time()

        if self.heatingStageIndex == 0:
            self._totalPreviousStageTime = 0.0

        self._times = []
        self._voltages = []

        self._startLeastSquareThread(previousTemperature)

        current = self.currents[self.heatingStageIndex]
        self.system.startHeatingWithCurrent(current, key=self)


    def _startLeastSquareThread(self, previousTemperature=None):
        """
        Starts a new :class:`~ops.calibration.leastsquare.LeastSquareThread`.
        If there was a heating stage before the one that is just being started,
        the results of the minization performed in that heating stage and the
        user's temperature measurement are used as part of the starting
        estimation for the minization.
        """
        stage = self.heatingStageIndex

        assert (previousTemperature == None) == (stage == 0)

        if stage == 0:
            est = getFirstStartingEstimates(self.currents[0])
        else:
            est = getSubsequentStartingEstimates(
                previousTemperature,
                self._leastSquareThread.solution,
                self.currents[stage] - self.currents[stage - 1])

        self._leastSquareThread = LeastSquareThread(est)
        self._leastSquareThread.start()


    def _checkHeatingProgress(self):
        """
        A *tick method* that requests a heating temperature measurement if
        :meth:`getProgress` returns ``1.0``.
        """
        self._times.append(time.time() - self._stageStartingTime)
        self._voltages.append(self.system.temperatureSensorVoltage)

        if self.getProgress() < 1.0:
            t, u = self._times, self._voltages
            self._leastSquareThread.refreshData(times=t, voltages=u)
        else:
            self._totalPreviousStageTime += self._times[-1]
            self._leastSquareThread.stop()
            self._sendTemperatureRequest()


    ###########################################################################
    # PROGRESS ESTIMATION                                                     #
    ###########################################################################

    #: The greatest difference between the estimated heating temperature and
    #: and the estimated final heating temperature that is small enough for a
    #: temperature measurement to be requested, in °C. This is a class
    #: attribute, but it can be set on an instance to override the default
    #: value.
    precision = 1.0


    def getProgress(self):
        """
        Estimates what fraction of the time required to finish the ongoing
        calibration stage has already passed. The estimate returned is in
        the range [``0.0``, ``1.0``]. If the calibration procedure's state
        is :data:`STATE_NOT_YET_STARTED` or :data:`STATE_DONE`, ``0.0`` and
        ``1.0`` are returned, respectively.
        """
        if self.state == STATE_NOT_YET_STARTED:
            return 0.0

        if self.state == STATE_MOVING_HEATER:
            return self._getHeaterMovementProgress(
                self.system.heaterPosition, self._initialHeaterPosition)

        if self.state == STATE_HEATING:
            solution = self._leastSquareThread.solution
            if solution == None:
                return 0.0
            else:
                return self._getHeatingProgress(
                    solution.startingTemperature,
                    solution.finalTemperature,
                    solution.tau,
                    self._times[-1])

        if self.state in (STATE_WAITING_FOR_TEMPERATURE, STATE_DONE):
            return 1.0


    def _getHeaterMovementProgress(self, position, initialPosition):
        """
        Estimates what fraction of the time required to finish the heater
        movement has already passed, given the heater position and initial
        heater position.
        """
        if initialPosition == 1.0:
            return 1.0
        else:
            return (position - initialPosition) / (1.0 - initialPosition)


    def _getHeatingProgress(self, t0, t1, tau, timePassed):
        """
        Estimates what fraction of the time required to finish the ongoing
        heating stage has already passed, given the starting temperature,
        final temperature, tau, and time already spent heating.
        """
        if t1 > t0:
            tt = t1 - self.precision
        elif t1 < t0:
            tt = t1 + self.precision
        else:
            return 1.0

        timeRequired = tau * -math.log(1 - (tt - t0) / (t1 - t0))
        progress = timePassed / timeRequired

        # If timePassed exceeds the time that is actually required to finish
        # the heating stage, progress will be greater than 1.0 here, so it
        # needs to be capped.
        return min(1.0, progress)


    def getExtendedProgress(self):
        """
        Returns a named tuple with the following attributes:

        * *stageProgress*, the estimated progress of the ongoing calibration
          stage, as a number in the range [``0.0``, ``1.0``] (equal to the
          return value of :meth:`getProgress`);
        * *stageTimeLeft*, the estimated amount of time remaining until the
          ongoing calibration stage is finished, in seconds, or ``None`` if
          no estimation is possible;
        * *totalProgress*, the estimated progress of the calibration procedure
          as a whole, as a number in the range [``0.0``, ``1.0``];
        * *totalTimeLeft*, the estimated amount of time remaining until the
          calibration procedure as a whole is finished, in seconds, or
          ``None`` if no estimation is possible.

        If the calibration procedure's state is :data:`STATE_NOT_YET_STARTED`
        or :data:`STATE_DONE`, the tuples ``(0.0, None, 0.0, None)`` and
        ``(1.0, None, 1.0, None)`` are returned, respectively.
        """
        if self.state == STATE_NOT_YET_STARTED:
            return ExtendedProgress(0.0, None, 0.0, None)

        if self.state == STATE_MOVING_HEATER:
            return ExtendedProgress(self.getProgress(), None, 0.0, None)

        if self.state in (STATE_HEATING, STATE_WAITING_FOR_TEMPERATURE):
            if len(self._times) == 0:   # TODO: Test
                return ExtendedProgress(0.0, None, 0.0, None)
            else:
                return self._getExtendedHeatingProgress(
                    self.getProgress(),
                    self.heatingStageIndex,
                    self.heatingStageCount,
                    self._times[-1],
                    self._times[-1] + self._totalPreviousStageTime)

        if self.state == STATE_DONE:
            return ExtendedProgress(1.0, None, 1.0, None)


    def _getExtendedHeatingProgress(self, sp, si, sn, stp, ttp):
        """
        Returns a named tuple of the extended progress estimation during
        heating, given the stage progress, stage index, number of stages
        needed, stage time passed, and total time passed.
        """
        # sp,  tp  : stage progress and total progress
        # stp, ttp : stage time passed and total time passed
        # stn      : stage time needed
        # astn     : average stage time needed
        # stl, ttl : stage time left and total time left
        # si       : stage index
        # sn       : stages needed
        if sp == 0.0 and si == 0:
            return ExtendedProgress(0.0, None, 0.0, None)

        if sp > 0.0:
            stn = stp / sp
        else:
            stn = (ttp - stp) / si   # si cannot be 0 here

        stl = stn - stp

        astn = (ttp - stp + stn) / (si + 1)
        ttl = stl + astn * (sn - si - 1)
        tp = ttp / (ttp + ttl)
        # was tp = (si + sp) / sn

        return ExtendedProgress(sp, stl, tp, ttl)


    ###########################################################################
    # REQUESTING TEMPERATURES                                                 #
    ###########################################################################

    def _sendTemperatureRequest(self):
        """
        Sends a :class:`~ops.calibration.event.TemperatureRequested` event.
        The :class:`CalibrationManager` then waits for someone to call
        :meth:`_temperatureReportCallback`, which is sent along with the
        event as the callback function.
        """
        self._state = STATE_WAITING_FOR_TEMPERATURE
        self.system.mediator.noteEvent(TemperatureRequested(
            self, self.system, self._temperatureReportCallback))


    def _temperatureReportCallback(self, temperature):
        """
        A callback method :meth:`_sendTemperatureRequest` sends along with
        the :class:`~ops.calibration.event.TemperatureRequested` event it
        sends. Called to report a temperature measurement (in °C).
        """
        if self.state != STATE_WAITING_FOR_TEMPERATURE:
            raise util.ApplicationError('unwanted temperature report')

        i = self.system.heatingCurrent
        u = self.system.temperatureSensorVoltage
        self.system.calibrationData.addMeasurement(i, u, temperature)

        if self.hasMoreHeatingStages:
            self._sendTemperatureRequestOverEvent()
            self._startHeatingStage(temperature)
        else:
            # _sendTemperatureRequestOverEvent will be called by _done.
            self._done(self._explainNoMoreHeatingStages())


    def _sendTemperatureRequestOverEvent(self):
        """
        Sends a :class:`~ops.calibration.event.TemperatureRequestOver` event.
        """
        self.system.mediator.noteEvent(
            TemperatureRequestOver(self, self.system))


###############################################################################
# CALIBRATION MANAGER STATES                                                  #
###############################################################################

#: Indicates that the calibration procedure has not yet started.
STATE_NOT_YET_STARTED = 0

#: Indicates that the calibration manager is waiting for the heater
#: to reach its foremost position.
STATE_MOVING_HEATER = 1

#: Indicates that the calibration manager is waiting for the heating
#: temperature to get sufficiently close to its final value for a
#: measurement to be taken.
STATE_HEATING = 2

#: Indicates that the calibration manager is waiting for the user
#: to take a temperature measurement.
STATE_WAITING_FOR_TEMPERATURE = 3

#: Indicates that the calibration procedure has ended.
STATE_DONE = 4


###############################################################################
# STATUS CODES                                                                #
###############################################################################

#: Indicates that the calibration procedure was aborted by the user.
STATUS_ABORTED = 0

#: Indicates that the calibration procedure was terminated when the
#: :class:`~ops.system.ProductionSystem`'s safe mode was triggered.
STATUS_SAFE_MODE_TRIGGERED = 1

#: Indicates that the calibration procedure was terminated because the next
#: heating current would exceed the :class:`~ops.system.ProductionSystem`'s
#: :attr:`~ops.system.ProductionSystem.maxHeatingCurrent`.
STATUS_INVALID_CURRENT = 2

#: Indicates that the calibration procedure sucessfully aquired temperatures
#: for all passed heating currents.
STATUS_FINISHED = 3


###############################################################################
# EXTENDED PROGRESS NAMED TUPLE                                               #
###############################################################################

ExtendedProgress = collections.namedtuple('ExtendedProgress',
    'stageProgress, stageTimeLeft, totalProgress, totalTimeLeft')
