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

import unittest

import util


class StringFromFloatTests(unittest.TestCase):
    """Tests for :func:`util.stringFromFloat`."""

    TESTS = (
        (0.0,   '0',    '0.00'),
        (1.0,   '1',    '1.00'),
        (1.001, '1',    '1.00'),
        (1.01,  '1.01', '1.01'),
        (1.1,   '1.1',  '1.10'),
        (1.101, '1.1',  '1.10'),
        (1,     '1',    '1.00'))

    def testPositive(self):
        """Tests the function with positive values."""
        for n, trim, nontrim in self.TESTS:
            self.assertEqual(util.stringFromFloat(n, 2, True),  trim)
            self.assertEqual(util.stringFromFloat(n, 2, False), nontrim)

    def testNegative(self):
        """Tests the function with negative values."""
        for n, trim, nontrim in self.TESTS[1:]:
            self.assertEqual(
                util.stringFromFloat(-n, 2, True),  u'\u2212' + trim)
            self.assertEqual(
                util.stringFromFloat(-n, 2, False), u'\u2212' + nontrim)

    def testNonNuber(self):
        """Tests the function with non-numeric arguments."""
        try:
            util.stringFromFloat('foo', 2, False)
        except TypeError:
            pass
        else:
            self.fail()

###############################################################################

class StringFromTimePeriodTests(unittest.TestCase):
    """Tests for :func:`util.stringFromTimePeriod`."""

    TESTS = (
        (   0, '0 seconds'),
        (   1, '1 second'),
        (   2, '2 seconds'),
        (  60, '1 minute'),
        (  61, '1 minute, 1 second'),
        (  62, '1 minute, 2 seconds'),
        ( 120, '2 minutes'),
        ( 121, '2 minutes, 1 second'),
        ( 122, '2 minutes, 2 seconds'),
        (3600, '1 hour'),
        (3601, '1 hour, 1 second'),
        (3602, '1 hour, 2 seconds'),
        (3660, '1 hour, 1 minute'),
        (3661, '1 hour, 1 minute, 1 second'),
        (3662, '1 hour, 1 minute, 2 seconds'),
        (3720, '1 hour, 2 minutes'),
        (3721, '1 hour, 2 minutes, 1 second'),
        (3722, '1 hour, 2 minutes, 2 seconds'),
        (7200, '2 hours'),
        (7201, '2 hours, 1 second'),
        (7202, '2 hours, 2 seconds'),
        (7260, '2 hours, 1 minute'),
        (7261, '2 hours, 1 minute, 1 second'),
        (7262, '2 hours, 1 minute, 2 seconds'),
        (7320, '2 hours, 2 minutes'),
        (7321, '2 hours, 2 minutes, 1 second'),
        (7322, '2 hours, 2 minutes, 2 seconds'))

    def testInteger(self):
        """Tests the function with integer arguments."""
        for seconds, expected in self.TESTS:
            self.assertEqual(util.stringFromTimePeriod(seconds), expected)

    def testFloat(self):
        """Tests the function with float arguments."""
        for seconds, expected in self.TESTS:
            if seconds > 0:
                seconds -= 0.9
                self.assertEqual(util.stringFromTimePeriod(seconds), expected)

    def testNegative(self):
        """Tests the function with negative arguments."""
        for argument in (-1, -0.1):
            try:
                util.stringFromTimePeriod(argument)
            except ValueError:
                pass
            else:
                self.fail()

    def testNonNumber(self):
        """Tests the function with non-numeric arguments."""
        try:
            util.stringFromTimePeriod('foo')
        except TypeError:
            pass
        else:
            self.fail()

###############################################################################

class LimitTests(unittest.TestCase):
    """Tests the :func:`limit` function."""

    TESTS = (
        ((-3.2, -2.0,  2.0), -2.0),
        ((-2.0, -2.0,  2.0), -2.0),
        ((-1.4, -2.0,  2.0), -1.4),
        (( 0.0, -2.0,  2.0),  0.0),
        (( 1.2, -2.0,  2.0),  1.2),
        (( 2.0, -2.0,  2.0),  2.0),
        (( 3.5, -2.0,  2.0),  2.0),
        ((-4.8, -2.0, None), -2.0),
        (( 8.6, -2.0, None),  8.6),
        ((-7.3, None,  2.0), -7.3),
        (( 6.3, None,  2.0),  2.0),
        ((-5.1, None, None), -5.1),
        (( 9.6, None, None),  9.6))

    def _intIfNotNone(self, n):
        return int(n) if n is not None else None

    def testFloat(self):
        """Tests the function with float arguments."""
        for arguments, expected in self.TESTS:
            result = util.limit(*arguments)
            self.assertEqual(result, expected)
            self.assertTrue(isinstance(result, float))

    def testInteger(self):
        """Tests the function with integer arguments."""
        for arguments, expected in self.TESTS:
            result = util.limit(*[self._intIfNotNone(n) for n in arguments])
            self.assertEqual(result, int(expected))
            self.assertTrue(isinstance(result, int))

    def testBadRange(self):
        """Tests the function with minValue > maxValue."""
        try:
            util.limit(2.0, 5.0, 1.0)
        except ValueError:
            pass
        else:
            self.fail()

###############################################################################

class RoundToMultipleTests(unittest.TestCase):
    """Tests the :func:`roundToMultiple` function."""

    TESTS = (
        ( 0, 12,  0),
        (12, 12, 12),
        (15, 12, 12),
        (18, 12, 24),
        (20, 12, 24),
        (24, 12, 24))

    def testInteger(self):
        """Tests the function with integer arguments."""
        for n, m, expected in self.TESTS:
            results = (
                (util.roundToMultiple( n,  m),  expected),
                (util.roundToMultiple(-n,  m), -expected),
                (util.roundToMultiple( n, -m),  expected),
                (util.roundToMultiple(-n, -m), -expected))
            for result, expected in results:
                self.assertEqual(result, expected)
                self.assertTrue(isinstance(result, int))

    def testFloat(self):
        """Tests the function with float arguments."""
        for test in self.TESTS:
            n, m, expected = (x / 100.0 for x in test)
            results = (
                (util.roundToMultiple( n,  m),  expected),
                (util.roundToMultiple(-n,  m), -expected),
                (util.roundToMultiple( n, -m),  expected),
                (util.roundToMultiple(-n, -m), -expected))
            for result, expected in results:
                self.assertEqual(result, expected)
                self.assertTrue(isinstance(result, float))

    def testMixed(self):
        """Tests the function with mixed arguments."""
        for n, m, expected in self.TESTS:
            results = (
                (util.roundToMultiple(float( n),  m),  expected),
                (util.roundToMultiple(float(-n),  m), -expected),
                (util.roundToMultiple(float( n), -m),  expected),
                (util.roundToMultiple(float(-n), -m), -expected),
                (util.roundToMultiple( n, float( m)),  expected),
                (util.roundToMultiple(-n, float( m)), -expected),
                (util.roundToMultiple( n, float(-m)),  expected),
                (util.roundToMultiple(-n, float(-m)), -expected))
            for result, expected in results:
                self.assertEqual(result, expected)
                self.assertTrue(isinstance(result, float))

    def testMultipleOfZero(self):
        """Attempts to find a multiple of zero."""
        try:
            util.roundToMultiple(12, 0)
        except ZeroDivisionError:
            pass
        else:
            self.fail()

###############################################################################

class WeakMethodTest(unittest.TestCase):
    """Tests the :class:`WeakMethod` class."""

    def testCall(self):
        """Tests the :meth:`__call__` method."""
        testClass = TestClass()
        weakMethod = util.WeakMethod(testClass.wrappedMethod)
        self.assertEqual(weakMethod(1, 2, 3), (1, 2, 3))
        testClass = None
        self.assertRaises(ReferenceError, weakMethod, 1, 2, 3)


    def testCallbackCall(self):
        """Checks that the callback is called."""
        self.callbackMethodCalled = False

        def callback(wm):
            self.assertEqual(weakMethod, wm)
            self.callbackMethodCalled = True

        testClass = TestClass()
        weakMethod = util.WeakMethod(testClass.wrappedMethod, callback)
        testClass = None
        self.assertTrue(self.callbackMethodCalled)
        del self.callbackMethodCalled


    def testIsSameMethod(self):
        """Tests the :meth:`isSameMethod` method."""
        testClass = TestClass()
        weakMethod = util.WeakMethod(testClass.wrappedMethod)

        self.assertTrue(weakMethod.isSameMethod(testClass.wrappedMethod))
        self.assertFalse(weakMethod.isSameMethod(TestClass().wrappedMethod))
        self.assertFalse(weakMethod.isSameMethod(testClass.someOtherMethod))



class TestClass(object):
    """Used by :class:`WeakMethodTest` to test :class:`WeakMethod` on."""
    def wrappedMethod(self, a, b, c):
        return a, b, c
    def someOtherMethod(self, x, y, z):
        pass
