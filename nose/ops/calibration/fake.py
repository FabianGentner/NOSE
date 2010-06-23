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

from ops.calibration.manager import *
from test import *


class FakeCalibrationManager(CalibrationManager):

    def __init__(self, system, currents):
        super(self.__class__, self).__init__(system, currents)
        self._ticks = 0
        self._leastSquareThread = Stub(None,
            refreshData=fun(None), stop=fun(None))


    def _checkHeaterPosition(self):
        """
        A *tick method* that checks whether the heater has reached its
        foremost position and proceeds with the next part of the calibration
        procedure if it has.
        """
        if self._ticks == 40:
            self._startHeatingStage()


    def _startHeatingStage(self, previousTemperature=None):
        self._ticks = 0
        super(self.__class__, self)._startHeatingStage(previousTemperature)


    def _startLeastSquareThread(self, previousTemperature=None):
        pass


    def getProgress(self):
        if self.state == STATE_NOT_YET_STARTED:
            return 0.0

        if self.state == STATE_MOVING_HEATER:
            self._ticks += 1
            return self._ticks / 40.0

        if self.state == STATE_HEATING:
            self._ticks += 1
            return self._ticks / 40.0

        if self.state in (STATE_WAITING_FOR_TEMPERATURE, STATE_DONE):
            return 1.0


