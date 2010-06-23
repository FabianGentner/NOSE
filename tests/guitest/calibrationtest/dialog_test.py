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
import weakref

import ops.system
import gui.calibration.dialog as gcd
import gui.widgets as widgets
import test.stubs


class AllTests(unittest.TestCase):
    """
    Tests for the gui.calibration.dialog module.
    """

    def setUp(self):
        self.mediatorStub = test.stubs.MediatorStub()
        self.system = ops.system.ProductionSystem(self.mediatorStub)
        self.dialogHandler = gcd.CalibrationDialogHandler(self.system)
        self.listBoxHandler = self.dialogHandler._listBoxHandler

        self.startCalibrationCalled = False
        self.abortCalibrationCalled = False

        def fakeStartCalibration(currents):
            self.startCalibrationCalled = True

        def fakeAbortCalibration():
            self.abortCalibrationCalled = True

        self.system.startCalibration = fakeStartCalibration
        self.system.abortCalibration = fakeAbortCalibration


    def tearDown(self):
        widgets.TESTING_DEFAULT_ANSWER = None
        widgets.TESTING_QUESTION_ASKED = False




    def testGC(self):
        """Make sure the classes are properly garbage-collected."""
        dialogHandlerReference = weakref.ref(self.dialogHandler)
        listBoxHandlerReference = weakref.ref(self.listBoxHandler)
        self.dialogHandler = None
        self.listBoxHandler = None
        gc.collect()
        self.assertEqual(dialogHandlerReference(), None)
        self.assertEqual(listBoxHandlerReference(), None)


    def testFixWidgetSizes(self):
        """Tests the _fixWidgetSizes method."""
        self.dialogHandler._fixWidgetSizes()
        # There's not much we can check without showing the dialog. Just make
        # sure there are no syntax errors, and that the initial visibilities
        # are restored when _fixWidgetSizes is done.
        self._checkState(calibrationInProgress=False)


    def testRunCalibrationClicked(self):
        """Tests the _runCalibrationClicked method."""
        self.dialogHandler._runCalibrationClicked(None)
        self.assertTrue(self.startCalibrationCalled)


    def testAbortCalibrationClicked(self):
        """Tests the _abortCalibrationClicked method."""
        widgets.TESTING_DEFAULT_ANSWER = True
        self.dialogHandler._abortCalibrationClicked(None)
        self.assertTrue(widgets.TESTING_QUESTION_ASKED)
        self.assertTrue(self.abortCalibrationCalled)


    def testWidgetSwitching(self):
        """Tests whether widgets are properly being switched around."""
        treeView = self.listBoxHandler._treeView

        # This assumes that there are at least three rows, and that row 1 has
        # at least three children. If the structure of the tree changes, the
        # numbers might have to be adjusted.
        child1 = self.dialogHandler._viewport.get_child()
        treeView.get_selection().select_path((2,1))
        child2 = self.dialogHandler._viewport.get_child()
        treeView.get_selection().select_path((1,2))
        child3 = self.dialogHandler._viewport.get_child()
        treeView.get_selection().select_path((2,1))
        child4 = self.dialogHandler._viewport.get_child()

        self.assertNotEqual(child1, child2)
        self.assertNotEqual(child1, child3)
        self.assertNotEqual(child1, child4)
        self.assertNotEqual(child2, child3)
        self.assertEqual(child2, child4)
        self.assertNotEqual(child3, child4)


    def testNoPath(self):
        """Tests unselecting all paths. (This case needs special handling.)"""
        selection = self.listBoxHandler._treeView.get_selection()
        treeModel, rows = selection.get_selected_rows()
        for row in rows:
            selection.unselect_path(row)


    def testStates(self):
        """
        Make sure widgets are hidden or shown depending on whether a
        calibration procedure is in progress.
        """
        self._checkState(calibrationInProgress=False)

        self.dialogHandler._switchState(calibrationInProgress=True)
        self._checkState(calibrationInProgress=True)

        self.dialogHandler._switchState(calibrationInProgress=False)
        self._checkState(calibrationInProgress=False)


    def testStatusLabelAfterCalibration(self):
        """
        Tests whether the status label is blanked when the calibration
        procedure finishes.
        """
        self.dialogHandler._switchState(calibrationInProgress=True)
        self.dialogHandler._statusLabel.set_text('Some arbitrary text.')
        self.dialogHandler._switchState(calibrationInProgress=False)
        self.assertEqual(self.dialogHandler._statusLabel.get_text(), '')


    def testRequestTemperature(self):
        """Tests the requestTemperature method."""
        self.dialogHandler._switchState(calibrationInProgress=True)
        self.dialogHandler._statusLabel.set_text('SAT')
        self.dialogHandler.requestTemperature(lambda temperature : None)
        self.assertNotEqual(self.dialogHandler._statusLabel.get_text(), 'SAT')
        self._checkSensitivity(
            self.dialogHandler._temperatureEntryWidgetHandler.widget, True)


    def _checkState(self, calibrationInProgress):
        """
        An utility method used by testStates to make sure widgets are hidden or
        shown depending on whether a calibration procedure is in progress.
        """
        cip = calibrationInProgress
        handler = self.dialogHandler
        self._checkSensitivity(handler._parameterWidgetHandler.widget, not cip)
        self._checkVisibility(handler._progressWidgetHandler.widget, cip)

        self._checkVisibility(handler._abortCalibrationButton, cip)
        self._checkVisibility(handler._runCalibrationButton, not cip)

        self._checkVisibility(handler._progressBar, cip)
        self._checkVisibility(handler._statusLabel, True)


    def _checkVisibility(self, widget, expected):
        """Checks whether the widget has the expected visibility."""
        self.assertEqual(widget.get_property('visible'), expected)


    def _checkSensitivity(self, widget, expected):
        """Checks whether the widget has the expected sensitivity."""
        self.assertEqual(widget.get_property('sensitive'), expected)


    def testConfirmAbortYes(self):
        """Tests the _confirmAbort method, assuming the user answers Yes."""
        widgets.TESTING_DEFAULT_ANSWER = True
        self.assertTrue(self.dialogHandler._confirmAbort())
        self.assertTrue(widgets.TESTING_QUESTION_ASKED)
        self.assertTrue(self.abortCalibrationCalled)


    def testConfirmAbortNo(self):
        """Tests the _confirmAbort method, assuming the user answers No."""
        widgets.TESTING_DEFAULT_ANSWER = False
        self.assertFalse(self.dialogHandler._confirmAbort())
        self.assertTrue(widgets.TESTING_QUESTION_ASKED)


    def testCloseNoCalibration(self):
        """Tests the _close method, assuming no calibration is in progress."""
        self.assertTrue(self.dialogHandler._close())
        self.assertFalse(widgets.TESTING_QUESTION_ASKED)


    def testCloseYes(self):
        """
        Tests the _close method, assuming a calibration procedure is in
        progress, and the user elects to close the dialog nevertheless.
        """
        widgets.TESTING_DEFAULT_ANSWER = True
        self.dialogHandler._system._calibrationManager = object()
        self.assertTrue(self.dialogHandler._close())
        self.assertTrue(widgets.TESTING_QUESTION_ASKED)
        self.assertTrue(self.abortCalibrationCalled)


    def testCloseNo(self):
        """
        Tests the _close method, assuming a calibration procedure is in
        progress, and the user elects not to close the dialog when asked.
        """
        widgets.TESTING_DEFAULT_ANSWER = False
        self.dialogHandler._system._calibrationManager = object()
        self.assertTrue(self.dialogHandler._close())
        self.assertTrue(widgets.TESTING_QUESTION_ASKED)
        self.assertFalse(self.abortCalibrationCalled)

