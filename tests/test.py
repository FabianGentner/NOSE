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

# FIXME: Rename

"""
Foo.
"""

class Stub(object):

    def __init__(self, real, **attributes):
        self.real = real
        self.log = []
        self.attributes = attributes


    def __getattr__(self, name):
        try:
            if self.real == None or hasattr(self.real, name):
                value = self.attributes[name]

                if isinstance(value, Can):
                    return value.uncan(name, self.log)
                else:
                    self.log.append((name, value))
                    return value
            else:
                raise StubError(
                    '%s does not have the attribute %s' % (self.real, name))

        except KeyError:
            raise AttributeError


class Can(object):
    pass


class once(Can):

    def __init__(self, value):
        self.value = value

    def uncan(self, name, log):
        try:
            value = self.value
            del self.value
            log.append((name, value))
            return value
        except AttributeError:
            raise StubException('%s has already been used' % name)


class queue(Can):

    def __init__(self, *values):
        self.values = list(reversed(values))

    def uncan(self, name, log):
        try:
            value = self.values.pop()
            log.append((name, value))
            return value
        except IndexError:
            raise StubException(
                'all values in %s have already been used' % name)


class fun(Can):

    def __init__(self, value):
        self.value = value

    def uncan(self, name, log):
        # TODO: kw is currently ignored
        def inner(*parameters, **kw):
            if isinstance(self.value, Can):
                value = self.value.uncan('return', [])
            else:
                value = self.value

            log.append((name, parameters, value))

            return value

        return inner


class StubError(Exception):
    pass




import unittest
import ops.calibration.data



#class Stub(object):
    #def __init__(self, realClass, **args):
        #self.__realclass__ = realClass
        #for name, value in args.items():
            #setattr(self, name, value)

    #def __getattribute__(self, name):
        #if name not in dir(object.__getattribute__(self, '__realclass__')):
            #raise AttributeError

        #can = object.__getattribute__(self, name)

        #if isinstance(can, list):
            #if len(can) > 0 and can[0] == 'fun':
                #if len(can) == 3 and can[2] == '...':
                    #return lambda *p: can[1]
                #else:
                    #ret = can[1]
                    #del can[1]
                    #return lambda *p: ret
            #if len(can) == 2 and can[1] == '...':
                #return can[0]
            #else:
                #answer = can[0]
                #del can[0]
                #return answer
        #else:
            #object.__delattr__(self, name)
            #return can



def wrapLogger(method):
    obj = method.__self__
    name = method.__name__
    logger = CallLogger(method)
    setattr(obj, name, logger)
    return logger


def replaceWithLogger(method, returnValues=None):
    obj = method.__self__
    name = method.__name__
    logger = CallLogger(returnValues=returnValues)
    setattr(obj, name, logger)
    return logger



class CallLogger(object):
    def __init__(self, function=None, returnValues=None, repeatReturn=False):
        assert function == None or (returnValues == None and not repeatReturn)
        self.log = []
        self.function = function
        self.returnValues = returnValues
        self.repeatReturn = repeatReturn

    def __call__(self, *parameters, **keywordParameters):
        if keywordParameters:
            if parameters:
                self.log.append((parameters, keywordParameters))
            else:
                self.log.append(keywordParameters)
        elif len(parameters) == 1:
            self.log.append(parameters[0])
        else:
            self.log.append(parameters)

        if self.function == None:
            if self.repeatReturn or self.returnValues == None:
                return self.returnValues
            else:
                returnValue = self.returnValues[0]
                self.returnValues = self.returnValues[1:]
                return returnValue
        else:
            return self.function(*parameters, **keywordParameters)


    def unwrap(self):
        setattr(self.function.__self__, self.function.__name__, self.function)



class FakeTime(object):

    def __init__(self, *times):
        self.times = list(times)

    def time(self):
        time = self.times[0]
        self.times = self.times[1:]
        return time


def makeCalibrationData():
    cd = ops.calibration.data.CalibrationData()
    cd.addMeasurement( 2.0, 0.2,  200.0)
    cd.addMeasurement( 4.0, 0.4,  400.0)
    cd.addMeasurement( 6.0, 0.6,  600.0)
    cd.addMeasurement( 8.0, 0.8,  800.0)
    cd.addMeasurement(10.0, 1.0, 1000.0)
    cd.addMeasurement(12.0, 1.2, 1200.0)
    cd.addMeasurement(14.0, 1.4, 1400.0)
    cd.addMeasurement(16.0, 1.6, 1600.0)
    cd.addMeasurement(18.0, 1.8, 1800.0)
    cd.addMeasurement(20.0, 2.0, 2000.0)
    return cd

