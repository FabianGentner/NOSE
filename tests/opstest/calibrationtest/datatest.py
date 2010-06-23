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

import itertools
import numpy
import sys
import unittest

from ops.calibration.data import *
from ops.calibration.event import *

import gui.mediator
import ops.system
import test
import util


class CalibrationManagerTests(unittest.TestCase):
    """
    Tests for the :class:`~ops.calibration.data.CalibrationData` class.
    """

    def setUp(self):
        self.mediator = gui.mediator.Mediator(logging=True)
        self.system = ops.system.ProductionSystem(self.mediator)
        self.cd = self.system.calibrationData
        self.mcLogger = test.wrapLogger(self.cd._measurementChanged)


    ###########################################################################
    # GENERAL ATTRIBUTES                                                      #
    ###########################################################################

    def testSystem(self):
        """Tests the :attr:`system` property."""
        freeCD = CalibrationData()

        # These operations must not raise errors.
        self.cd.system = self.system
        freeCD.system = None

        class FakeSystem(object): pass
        fakeSystem1 = FakeSystem()
        fakeSystem2 = FakeSystem()
        cd = CalibrationData()
        fakeSystem1.calibrationData = cd
        cd.system = fakeSystem1
        self.assertTrue(cd.system is fakeSystem1)

        fakeSystem1.calibrationData = None
        fakeSystem2.calibrationData = cd
        cd.system = fakeSystem2
        self.assertTrue(cd.system is fakeSystem2)

        fakeSystem2.calibrationData = CalibrationData()
        cd.system = None
        self.assertTrue(cd.system is None)


    def testSystemErrors(self):
        """Tests the exceptions raised by setting :attr:`system`."""
        otherMediator = gui.mediator.Mediator()
        otherSystem = ops.system.ProductionSystem(otherMediator)
        freeCD = CalibrationData()

        # the object is still associated with a system
        self.assertRaises(util.ApplicationError,
            setattr, self.cd, 'system', None)
        self.assertRaises(util.ApplicationError,
            setattr, self.cd, 'system', otherSystem)

        # the object is not associated with the new system
        self.assertRaises(util.ApplicationError,
            setattr, freeCD, 'system', self.system)


    def testFileName(self):
        """Tests the :attr:`fileName` property."""
        self.assertEqual(self.cd.fileName, None)
        self.cd.fileName = 'some random text'
        self.assertEqual(self.cd.fileName, 'some random text')
        self.cd.fileName = None
        self.assertEqual(self.cd.fileName, None)


    ###########################################################################
    # MEASUREMENTS                                                            #
    ###########################################################################

    def testAddMeasurement(self):
        """Tests the :meth:`addMeasurement` method."""
        currents = (4.0, 2.0, 8.0, 6.0)
        expected = {}
        for count, current in enumerate(currents, start=1):
            measurement = (current, current / 10, current * 100)
            expected[current] = measurement
            self.cd.addMeasurement(*measurement)
            self.assertEqual(self.cd._measurements[current], measurement)
            self.assertEqual(self.cd._measurements, expected)
            self.assertEqual(len(self.mcLogger.log), count)


    def testAddIntegerMeasurement(self):
        """Tests the :meth:`addMeasurement` method with integer arguments."""
        currents = (4, 2, 8, 6)
        expected = {}
        for count, current in enumerate(currents, start=1):
            measurement = (current, current / 10, current * 100)
            floatMeasurement = tuple(float(n) for n in measurement)
            expected[float(current)] = floatMeasurement
            self.cd.addMeasurement(*measurement)
            self.assertEqual(
                self.cd._measurements[float(current)], floatMeasurement)
            self.assertEqual(self.cd._measurements, expected)
            self.assertEqual(len(self.mcLogger.log), count)


    def testAddMeasurementsReplace(self):
        """Tests replacing a measurement in :meth:`addMeasurement`."""
        self._addSomeMeasurements()
        self.cd.addMeasurement(4.0, 0.2, 200.0)
        self.assertEqual(self.cd._measurements[4.0], (4.0, 0.2, 200.0))
        self.assertEqual(len(self.mcLogger.log), 1)


    def testRemoveMeasurement(self):
        """Tests the :meth:`removeMeasurement` method."""
        self._addSomeMeasurements()
        self.cd.removeMeasurement(4.0)
        self.assertTrue(4.0 not in self.cd._measurements)
        self.assertEqual(len(self.mcLogger.log), 1)


    def testRemoveIntegerMeasurement(self):
        """Tests the :meth:`removeMeasurement` method with an integer."""
        self._addSomeMeasurements()
        self.cd.removeMeasurement(4)
        self.assertTrue(4.0 not in self.cd._measurements)
        self.assertEqual(len(self.mcLogger.log), 1)


    def testRemoveMeasurementError(self):
        """
        Tests the error handing of the :meth:`removeMeasurements` method.
        """
        self._addSomeMeasurements()
        self.assertRaises(KeyError, self.cd.removeMeasurement, 5.0)
        self.assertEqual(len(self.mcLogger.log), 0)


    def testMeasurementChanged(self):
        """Tests the :meth:`_measurementChanged` method."""
        eventCount = len(self.mediator.eventsNoted)
        rpLogger = test.wrapLogger(self.cd._recalculatePolynomials)

        self.cd._measurementChanged()
        self.assertEqual(len(rpLogger.log), 1)
        self.assertEqual(len(self.mediator.eventsNoted), eventCount + 1)
        self.assertEqual(self.mediator.eventsNoted[-1],
            CalibrationDataChanged(self.system, self.cd))

        self.system.calibrationData = CalibrationData()
        self.assertEqual(len(self.mediator.eventsNoted), eventCount + 2)

        # cd is now free; recalculate poynomials, but send no events.
        self.cd._measurementChanged()
        self.assertEqual(len(rpLogger.log), 2)
        self.assertEqual(len(self.mediator.eventsNoted), eventCount + 2)


    def testMeasurementsProperties(self):
        """Test the measurements-related properties."""
        self._addSomeMeasurements()
        self.assertEqual(
            self.cd.measurements, ((2.0, 0.2, 200.0), (4.0, 0.4, 400.0),
                (6.0, 0.6, 600.0), (8.0, 0.8, 800.0)))
        self.assertEqual(
            self.cd.heatingCurrents, (2.0, 4.0, 6.0, 8.0))
        self.assertEqual(
            self.cd.temperatureSensorVoltages, (0.2, 0.4, 0.6, 0.8))
        self.assertEqual(
            self.cd.temperatures, (200.0, 400.0, 600.0, 800.0))


    def testHasMeasurements(self):
        """Tests the :attr:`hasMeasurements` property."""
        self.assertFalse(self.cd.hasMeasurements)
        self.cd.addMeasurement(2.0, 0.2, 200.0)
        self.assertTrue(self.cd.hasMeasurements)
        self.cd.removeMeasurement(2.0)
        self.assertFalse(self.cd.hasMeasurements)


    ###########################################################################
    # ESTIMATION FUNCTIONS                                                    #
    ###########################################################################

    def testIsComplete(self):
        """Tests the :attr:`isComplete` property."""
        poly = numpy.poly1d([0.1, -0.5, 2.5, -12.5, 0.0])
        for product in itertools.product([True, False], repeat=3):
            x, y, z = product
            self.cd._currentFromTargetTemperature = poly if x else None
            self.cd._finalTemperatureFromCurrent = poly if y else None
            self.cd._temperatureFromVoltage = poly if z else None
            self.assertEqual(self.cd.isComplete, x and y and z)


    def testEstimationFunctions(self):
        """Test the accesors for the estimation functions."""
        ift = numpy.poly1d([0.1, -0.5, 2.5, -12.5, 0.0])
        tfi = numpy.poly1d([0.1, -0.5, 2.5, -12.5, 0.1])
        tfu = numpy.poly1d([0.1, -0.5, 2.5, -12.5, 0.2])
        self.cd._currentFromTargetTemperature = ift
        self.cd._finalTemperatureFromCurrent = tfi
        self.cd._temperatureFromVoltage = tfu
        self.assertEqual(self.cd.getCurrentFromTargetTemperature(10.0), 625.0)
        self.assertEqual(self.cd.getFinalTemperatureFromCurrent(10.0), 625.1)
        self.assertEqual(self.cd.getTemperatureFromVoltage(10.0), 625.2)


    def testEstimationFunctionsError(self):
        """Tests the accessors when the estimation function aren't fitted."""
        functions = (
            self.cd.getCurrentFromTargetTemperature,
            self.cd.getFinalTemperatureFromCurrent,
            self.cd.getTemperatureFromVoltage)
        for f in functions:
            self.assertRaises(ops.error.NotCalibratedError, f, 10.0)


    ###########################################################################
    # FITTING                                                                 #
    ###########################################################################

    def testRecalculatePolynomials(self):
        """Tests the :meth:`_recalculatePolynomials` method."""
        i = [1.0,     2.0,    3.0,    4.0,   5.0,    6.0,     7.0]
        u = [0.1,     0.15,   0.25,   0.4,   0.6,    0.85,    1.15]
        t = [300.0, 350.0,  450.0,  600.0, 800.0, 1050.0,  1400.0]

        for n in xrange(7):
            self.cd.addMeasurement(i[n], u[n], t[n])

        iftx = self.cd._fit(t, i)
        tfix = self.cd._fit(i, t)
        tfux = self.cd._fit(u, t)

        self.assertEqual(self.cd._currentFromTargetTemperature, iftx)
        self.assertEqual(self.cd._finalTemperatureFromCurrent, tfix)
        self.assertEqual(self.cd._temperatureFromVoltage, tfux)


    def testFit(self):
        """Tests the :meth:`_fit` method."""
        self.cd.minMeasurementsForEstimation = 7
        self.cd.polynomialDegree = 2
        x, y = self._getSomePoints(0.1, -0.75, 12.0)
        coefficients = self.cd._fit(x, y).c
        self.assertAlmostEqual(coefficients[0], 0.1)
        self.assertAlmostEqual(coefficients[1], -0.75)
        self.assertAlmostEqual(coefficients[2], 12.0)


    def testFitNotEnoughMeasurements(self):
        """Tests the :meth:`_fit` method with too few measurements."""
        self.cd.minMeasurementsForEstimation = 100
        self.cd.polynomialDegree = 2
        x, y = self._getSomePoints(0.1, -0.75, 12.0)
        # WORKAROUND: poly1d's __eq__ method is broken.
        self.assertTrue(self.cd._fit(x, y) is None)


    def testFitRankWarning(self):
        """Tests the :meth:`_fit` method when there is a RankWarning."""
        self.cd.minMeasurementsForEstimation = 0
        self.cd.polynomialDegree = 15
        x, y = self._getSomePoints(0.1, -0.75, 12.0)

        # Make sure the warning isn't printed to sys.stderr.
        stderrOld = sys.stderr
        try:
            sys.stderr = None
            # WORKAROUND: poly1d's __eq__ method is broken.
            self.assertTrue(self.cd._fit(x, y) is None)
        except AttributeError:
            # Someone tried to use sys.stderr.
            self.fail()
        finally:
            sys.stderr = stderrOld


    ###########################################################################
    # TEST UTILIY METHODS                                                     #
    ###########################################################################

    def _addSomeMeasurements(self):
        """Adds a couple of measurements to :attr:`cd`."""
        for current in (2.0, 8.0, 4.0, 6.0):
            self.cd.addMeasurement(current, current / 10, current * 100)
        self.mcLogger.log = []


    def _getSomePoints(self, *coefficients):
        """Generates a couple of data points using the given coefficients."""
        poly = numpy.poly1d(coefficients)
        x = [float(n) for n in xrange(12)]
        y = [poly(n) for n in x]
        return x, y




class CalibrationManagerPersistenceTest(unittest.TestCase):
    """
    Tests for the persistence functions in the ops.calibration.data module.
    """

    def setUp(self):
        self.mediator = gui.mediator.Mediator(logging=True)
        self.system = ops.system.ProductionSystem(self.mediator)
        self.cd = self.system.calibrationData


    def testRoundTrip(self):
        """Checks that calibration data survives a round trip to XML."""
        self.system.performMagicCalibration()
        result = fromXML(toXML(self.cd))
        self.assertEqual(result.measurements, self.cd.measurements)


    def testDocumentWithNoMeasurements(self):
        """
        Tests the :func:`fromXML` function with a document that does not
        contain any measurements.
        """
        self.assertNotEqual(
            fromXML(self.DOCUMENT_TEMPLATE % ''), None)


    def testFromXMLWithBadDocuments(self):
        """Tests the :func:`fromXML` function with some bad XML documents."""
        badDocuments = (
            '',
            'this is not an XML document',
            '<?xml version="1.0" ?><unexpected></unexpected>')
        for document in badDocuments:
            self.assertEqual(fromXML(document), None)


    def testFromXMLWithMissingValueTags(self):
        """Tests the :func:`fromXML` function with missing value tags."""
        for badIndex in xrange(3):
            measurement = '<measurement>'
            for index in xrange(3):
                if index != badIndex:
                    tag = self.TAGS[index]
                    measurement += '<%s>%s</%s>' % (tag, 2.0, tag)
            measurement += '</measurement>'
            document = self.DOCUMENT_TEMPLATE % measurement
            self.assertEqual(fromXML(document), None)


    def testFromXMLWithBadValues(self):
        """Tests the :func:`fromXML` function with bad measurement values."""
        for badValue in ('', 'foo', 'nan', '+inf', '-inf'):
            for badIndex in xrange(3):
                measurement = '<measurement>'
                for index in xrange(3):
                    tag = self.TAGS[index]
                    if index == badIndex:
                        measurement += '<%s>%s</%s>' % (tag, badValue, tag)
                    else:
                        measurement += '<%s>%s</%s>' % (tag, 2.0, tag)
                measurement += '</measurement>'
                document = self.DOCUMENT_TEMPLATE % measurement
                self.assertEqual(fromXML(document), None)


    TAGS = ('current', 'voltage', 'temperature')

    DOCUMENT_TEMPLATE = (
        '<?xml version="1.0" ?><calibration-data>%s</calibration-data>')

