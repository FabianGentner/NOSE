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










class DeviceInterfaceStub(object):
    """
    A stub-object intended for use in place of a :class:`DeviceInterface`
    that provides canned answers for some property accesses.
    """
    def __init__(self, **args):
        for name, value in args.items():
            if hasattr(value, '__iter__'):
                value = list(reversed(value))
            setattr(self, name, value)

    @property
    def temperatureSensorVoltage(self):
        return self.voltages.pop()

    @property
    def heaterPosition(self):
        return self.positions.pop()

    def startHeatingWithCurrent(self, current):
        pass

    def startHeaterMovement(self, targetPosition):
        pass



class ProductionSystemStub(object):
    """
    A stub-object intended for use in place of a :class:`ProductionSystem`
    that provides canned answers for some property accesses.
    """
    def __init__(self, **args):
        for name, value in args.items():
            if hasattr(value, '__iter__'):
                value = list(reversed(value))
            setattr(self, name, value)

    @property
    def temperatureSensorVoltage(self):
        return self.voltages.pop()

    @property
    def heaterPosition(self):
        return self.positions.pop()






import weakref


# FIXME: Deprecated!
class MediatorStub(object):
    def __init__(self):
        self.addTimeoutCalls = []
        self.addListenerCalls = []
        self.noteEventCalls = []

    def addTimeout(self, timeout, callback):
        self.addTimeoutCalls.append((timeout, callback))

    def addListener(self, listener, *eventClasses):
        self.addListenerCalls.append(
            (weakref.proxy(listener), eventClasses))

    def noteEvent(self, event):
        self.noteEventCalls.append(event)

    def countEvents(self, eventClass):
        for number, call in enumerate(reversed(self.noteEventCalls)):
            if not isinstance(call, eventClass):
                return number
        else:
            return len(self.noteEventCalls)
