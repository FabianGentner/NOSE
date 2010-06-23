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
This module contains the :class:`CalibrationData` class, which encapsulates
the data collected during calibration, and a set of functions used to save
and load instances of this class.
"""

import math
import numpy
import warnings
import xml.dom.minidom

import ops.error
import ops.calibration.event
import util


###############################################################################
# CALIBRATION DATA                                                            #
###############################################################################

class CalibrationData(object):
    """
    Encapsulates the data collected during calibration. The calibration
    data consists of a list of the measurements (accessible using the
    :attr:`measurements` property) and a set of three estimation functions:
    :meth:`getCurrentFromTargetTemperature`,
    :meth:`getFinalTemperatureFromCurrent`, and
    :meth:`getTemperatureFromVoltage`.

    These are fitted to the measurements taken during calibration (using
    :func:`numpy.polyfit`) if at least :attr:`minMeasurementsForEstimation`
    measurements have been taken. To check whether the functions have been
    sucessfully fitted, use :attr:`isComplete`.

    When measurements are added to or removed from the calibration data,
    the estimation functions are automatically refitted.
    """

    ###########################################################################
    # GENERAL ATTRIBUTES                                                      #
    ###########################################################################

    def __init__(self):
        """
        Initializes a new instance of this class.
        """
        self._fileName = None
        self._system = None
        self._measurements = {}
        self._currentFromTargetTemperature = None
        self._finalTemperatureFromCurrent = None
        self._temperatureFromVoltage = None


    @property
    def system(self):
        """
        The :class:`~ops.system.ProductionSystem` whose calibration data the
        instance holds, or ``None``. If the instance associated with a system
        is changed, this parameter is automatically updated. Otherwise, it
        is read-only.
        """
        return self._system


    @system.setter
    def system(self, newSystem):
        # The setter for the :attr:`system` property.
        if self._system is newSystem:
            return
        elif self._system != None and self._system.calibrationData is self:
            raise util.ApplicationError('the CalibrationData object '
                'is still associated with a ProductionSystem')
        elif newSystem != None and newSystem.calibrationData is not self:
            raise util.ApplicationError('the CalibrationData object '
                'is not actually associated with the new ProductionSystem')
        else:
            self._system = newSystem


    @property
    def fileName(self):
        """
        The name of the file the instance has last been saved to, or the name
        of the file the instance has been read from, or ``None``.

        :class:`CalibrationData` itself does not use this attribute at all;
        it needs to be kept up to date by the client code responsible
        for saving and loading.
        """
        return self._fileName


    @fileName.setter
    def fileName(self, newFileName):
        # The setter for the :attr:`fileName` property.
        self._fileName = newFileName


    ###########################################################################
    # MEASUREMENTS                                                           #
    ###########################################################################

    def addMeasurement(self, current, voltage, temperature):
        """
        Adds a new measurement to the calibration data. Arguments are the
        heating current used for the measurement (in mA), and the final
        temperature sensor voltage (in V) and final temperature (in °C)
        that are reached with that current. Any measurements for that current
        that may have been added previously are replaced.

        Also recalculates the estimation functions, and sends
        a :class:`~ops.calibration.event.CalibrationDataChanged` event if the
        instance is associated with a :class:`~ops.system.ProductionSystem`.
        """
        i, u, t = float(current), float(voltage), float(temperature)
        self._measurements[i] = (i, u, t)
        self._measurementChanged()


    def removeMeasurement(self, current):
        """
        Removes the measurements taken for the given heating current (in mA)
        from the calibration data. Raises a :exc:`KeyError` if there are no
        measurements for that current.

        Also recalculates the estimation functions, and sends
        a :class:`~ops.calibration.event.CalibrationDataChanged` event if the
        instance is associated with a :class:`~ops.system.ProductionSystem`.
        """
        del self._measurements[current]
        self._measurementChanged()


    def _measurementChanged(self):
        """
        Called when the a measurement has been added to or deleted from
        :attr:`measurements`. Calls :meth:`_recalculatePolynomials`, and
        sends a :class:`~ops.calibrationevent.CalibrationDataChanged` event
        if :attr:`system` is set.
        """
        self._recalculatePolynomials()

        if self._system != None:
            assert self._system.calibrationData is self
            self._system.mediator.noteEvent(
                ops.calibration.event.CalibrationDataChanged(
                    self._system, self))


    @property
    def measurements(self):
        """
        A tuple of tuples that each contain the heating current,
        final temperature sensor voltage, and final heating temperature
        for a measurement that is part of the calibration data. The
        tuple's items are ordered by their heating currents. Read-only.
        """
        return tuple(sorted(self._measurements.values()))


    @property
    def heatingCurrents(self):
        """
        A sorted tuple of the heating currents the measurements that are part
        of the calibration data have been taken for. Read-only.
        """
        return tuple(m[0] for m in self.measurements)


    @property
    def temperatureSensorVoltages(self):
        """
        A tuple of the temperature sensor voltages that have been measured
        during calibration, sorted by the heating currents they have been
        measured for. Read-only.
        """
        return tuple(m[1] for m in self.measurements)


    @property
    def temperatures(self):
        """
        A tuple of the heating temperatures that have been measured during
        calibration, sorted by the heating currents they have been measured
        for. Read-only.
        """
        return tuple(m[2] for m in self.measurements)


    @property
    def hasMeasurements(self):
        """
        Indicates whether the instance has at least one measurement.
        """
        return len(self._measurements) > 0


    ###########################################################################
    # ESTIMATION FUNCTIONS                                                    #
    ###########################################################################

    # WORKAROUND: numpy.poly1d's __eq__ and __ne__ methods are broken:
    #             "p == None" and "p != None" each raises an AttributeError.
    #             Therefore, we must use "p is None" or "p is not None".

    @property
    def isComplete(self):
        """
        Indicates whether all three estimations functions have been
        sucessfully fitted. Read-only.
        """
        return (self._currentFromTargetTemperature is not None
            and self._finalTemperatureFromCurrent is not None
            and self._temperatureFromVoltage is not None)


    # FIXME: Document.

    @property
    def currentFromTargetTemperatureCoefficients(self):
        if self.isComplete:
            return tuple(self._currentFromTargetTemperature)
        else:
            return None


    @property
    def finalTemperatureFromCurrentCoefficients(self):
        if self.isComplete:
            return tuple(self._finalTemperatureFromCurrent)
        else:
            return None


    @property
    def temperatureFromVoltageCoefficients(self):
        if self.isComplete:
            return tuple(self._temperatureFromVoltage)
        else:
            return None


    def getCurrentFromTargetTemperature(self, targetTemperature):
        """
        Estimates the heating current (in mA) necessary for the heater
        to reach, but not exceed, a given target temperature (in °C).
        Raises a :exc:`~ops.error.NotCalibratedError` if the estimation
        function could not be fitted.
        """
        # TODO: Should be not self.isComplete
        if self._currentFromTargetTemperature is None:
            raise ops.error.NotCalibratedError()
        else:
            return self._currentFromTargetTemperature(targetTemperature)


    def getFinalTemperatureFromCurrent(self, current):
        """
        Estimates the temperature (in °C) that the heater will reach,
        but not exceed, for a given heating current (in mA).
        Raises a :exc:`~ops.error.NotCalibratedError` if the estimation
        function could not be fitted.
        """
        if self._finalTemperatureFromCurrent is None:
            raise ops.error.NotCalibratedError()
        else:
            return self._finalTemperatureFromCurrent(current)


    def getTemperatureFromVoltage(self, voltage):
        """
        Estimates the temperature (in °C) that corresponds to a given
        temperature sensor voltage (in V).
        Raises a :exc:`~ops.error.NotCalibratedError` if the estimation
        function could not be fitted.
        """
        if self._temperatureFromVoltage is None:
            raise ops.error.NotCalibratedError()
        else:
            return self._temperatureFromVoltage(voltage)


    ###########################################################################
    # FITTING                                                                 #
    ###########################################################################

    #: The degree of the polynomials that make up the estimation functions.
    #: This is a class attribute, but can be set on an instance to override
    #: the default value.
    polynomialDegree = 4

    #: The number of measurements that is required before the estimation
    #: functions are fitted. This is a class attribute, but can be set on
    #: an instance to override the default value.
    minMeasurementsForEstimation = 5


    def _recalculatePolynomials(self):
        """
        Recalculates the estimation functions. The actual work is done by
        :meth:`_fit`.
        """
        currents = self.heatingCurrents
        voltages = self.temperatureSensorVoltages
        temperatures = self.temperatures

        self._currentFromTargetTemperature = self._fit(temperatures, currents)
        self._finalTemperatureFromCurrent = self._fit(currents, temperatures)
        self._temperatureFromVoltage = self._fit(voltages, temperatures)


    def _fit(self, x, y):
        """
        Returns a :class:`numpy.poly1d` instance fitted to the passed points
        using :func:`numpy.polyfit` and the degree :attr:`polynomialDegree`.

        If fewer than :attr:`minMeasurementsForEstimation` points are passed,
        or if :func:`numpy.polyfit` issues a :exc:`numpy.RankWarning`, ``None``
        is returned instead. :exc:`numpy.RankWarning`\s that may be issued
        are not printed to :attr:`sys.stderr`.
        """
        if len(x) < self.minMeasurementsForEstimation:
            return None

        with warnings.catch_warnings():
            warnings.simplefilter('error')
            try:
                return numpy.poly1d(numpy.polyfit(x, y, self.polynomialDegree))
            except numpy.RankWarning:
                return None


###############################################################################
# PERSISTENCE FUNCTIONS                                                       #
###############################################################################

# Check the documentation for information on the file format.

def toXML(calibrationData):
    """
    Creates an XML document from the given :class:`CalibrationData` object
    and returns it as a string.
    """
    measurements = calibrationData.measurements

    implementation = xml.dom.minidom.getDOMImplementation()

    document = implementation.createDocument(None, 'calibration-data', None)
    top = document.documentElement

    names = ('current', 'voltage', 'temperature')

    for m in measurements:
        node = document.createElement('measurement')
        for i in range(3):
            child = document.createElement(names[i])
            child.appendChild(document.createTextNode(str(m[i])))
            node.appendChild(child)
        top.appendChild(node)

    return document.toxml()


def fromXML(string):
    """
    Creates a :class:`CalibrationData` object from the given string, which must
    be a valid XML document.

    If an error occurs while parsing the document, the function returns
    ``None``.
    """
    cd = CalibrationData()

    try:
        document = xml.dom.minidom.parseString(string)
        top = document.documentElement

        if top.tagName != 'calibration-data':
            return None

        names = ('current', 'voltage', 'temperature')

        for node in top.getElementsByTagName('measurement'):
            data = [None, None, None]

            for i in range(3):
                children = node.getElementsByTagName(names[i])
                value = float(children[0].firstChild.nodeValue)

                if math.isnan(value) or math.isinf(value):
                    return None

                data[i] = value

            cd.addMeasurement(*data)
    except Exception:
        return None
    else:
        return cd
