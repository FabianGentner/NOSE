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

import gtk
import os
import unittest

import gui.actions
import gui.io
import gui.main
import gui.widgets
import ops.system
import ops.calibration.data
import stubs
import test


class AllTests(unittest.TestCase):
    """
    Tests for the gui.actions module.
    """

    # TODO: Should also test NoseAction itself.
    # TODO: Should test sensitivity.


    def setUp(self):
        self.mediatorStub = stubs.MediatorStub()
        self.system = ops.system.ProductionSystem(self.mediatorStub)
        self.mainWindowHandler = gui.main.MainWindowHandler(
            self.mediatorStub, self.system)
        self.actionGroup = gtk.ActionGroup('Test')
        self.p = (self.mainWindowHandler, self.actionGroup)
        gui.widgets.TESTING_SUPPRESS_REPORTS = True


    def tearDown(self):
        gui.widgets.TESTING_SUPPRESS_REPORTS = False
        gui.widgets.TESTING_REPORT = None
        gui.widgets.TESTING_REPORT_ID = None
        gui.widgets.TESTING_DEFAULT_ANSWER = None
        gui.widgets.TESTING_QUESTION_ASKED = False



    def testQuitAction(self):
        """Tests the QuitAction class."""
        def fakeDestroy(): self.destroyCalled = True
        self.mainWindowHandler.destroy = fakeDestroy
        action = gui.actions.QuitAction(*self.p)
        action.activate()
        self.assertTrue(self.destroyCalled)


    def testShowCalibrationDialogAction(self):
        """Tests the ShowCalibrationDataAction class."""
        def fakeShowCalibrationDialog():
            self.showCalibrationDialogCalled = True
        self.mainWindowHandler.showCalibrationDialog = \
            fakeShowCalibrationDialog
        action = gui.actions.ShowCalibrationDialogAction(*self.p)
        action.activate()
        self.assertTrue(self.showCalibrationDialogCalled)


    def testLoadCalibrationDataAction(self):
        """Tests the LoadCalibrationDataAction class."""
        action = gui.actions.LoadCalibrationDataAction(*self.p)
        for new in (None, ops.calibration.data.CalibrationData()):
            if new is not None:
                new.fileName = 'should not be used'
            old = self.system.calibrationData
            self.installFakeIOFunctions(new)
            try:
                action.activate()
                self.assertEqual(self.loadParameters, (
                    'CalibrationData',
                    None,
                    self.mainWindowHandler._window))
                if new is None:
                    self.assertEqual(self.system.calibrationData, old)
                else:
                    self.assertEqual(self.system.calibrationData, new)
            finally:
                self.uninstallFakeIOFunctions()


    def testSaveCalibrationDataAction(self):
        """Tests the SaveCalibrationDataAction class."""
        action = gui.actions.SaveCalibrationDataAction(*self.p)
        cd = self.system.calibrationData
        cd.addMeasurement(1.0, 2.0, 3.0)
        for name in (None, 'should be used'):
            cd.fileName = name
            self.system.calibrationData = cd
            self.installFakeIOFunctions()
            try:
                action.activate()
                self.assertEqual(self.saveParameters, (
                    cd,
                    'CalibrationData',
                    name,
                    self.mainWindowHandler._window))
            finally:
                self.uninstallFakeIOFunctions()


    def testSaveCalibrationDataActionWithNoData(self):
        """Tests the illegal activation of a SaveCalibrationDataAction."""
        action = gui.actions.SaveCalibrationDataAction(*self.p)
        action.activate()
        self.assertEqual(gui.widgets.TESTING_REPORT_ID, 'illegal activation')


    def testSaveCalibrationDataAsAction(self):
        """Tests the SaveCalibrationDataAsAction class."""
        action = gui.actions.SaveCalibrationDataAsAction(*self.p)
        cd = self.system.calibrationData
        cd.addMeasurement(1.0, 2.0, 3.0)
        for name in (None, 'should not be used'):
            cd.fileName = name
            self.system.calibrationData = cd
            self.installFakeIOFunctions()
            try:
                action.activate()
                self.assertEqual(self.saveParameters, (
                    cd,
                    'CalibrationData',
                    None,
                    self.mainWindowHandler._window))
            finally:
                self.uninstallFakeIOFunctions()


    def testSaveCalibrationDataAsActionWithNoData(self):
        """Tests the illegal activation of a SaveCalibrationDataAsAction."""
        action = gui.actions.SaveCalibrationDataAsAction(*self.p)
        action.activate()
        self.assertEqual(gui.widgets.TESTING_REPORT_ID, 'illegal activation')


    def testClearCalibrationDataActionYes(self):
        """
        Tests activating a ClearCalibrationDataAsAction and answering Yes
        to the prompt.
        """
        action = gui.actions.ClearCalibrationDataAction(*self.p)
        cd = self.system.calibrationData
        cd.addMeasurement(1.0, 2.0, 3.0)
        gui.widgets.TESTING_DEFAULT_ANSWER = True
        action.activate()
        self.assertTrue(gui.widgets.TESTING_QUESTION_ASKED)
        self.assertNotEqual(cd, self.system.calibrationData)
        self.assertFalse(self.system.calibrationData.hasMeasurements)


    def testClearCalibrationDataActionNo(self):
        """
        Tests activating a ClearCalibrationDataAction and answering No
        to the prompt.
        """
        action = gui.actions.ClearCalibrationDataAction(*self.p)
        cd = self.system.calibrationData
        cd.addMeasurement(1.0, 2.0, 3.0)
        gui.widgets.TESTING_DEFAULT_ANSWER = False
        action.activate()
        self.assertTrue(gui.widgets.TESTING_QUESTION_ASKED)
        self.assertTrue(cd.hasMeasurements)


    def testClearCalibrationDataActionWithNoData(self):
        """Tests the illegal activation of a ClearCalibrationDataAction."""
        action = gui.actions.ClearCalibrationDataAction(*self.p)
        action.activate()
        self.assertEqual(gui.widgets.TESTING_REPORT_ID, 'illegal activation')


    def testCreateActionGroup(self):
        """
        Does some minimal testing of the createActionGroup function.
        The tests for the gui.main module should do some more thorough testing.
        """
        gui.actions.createActionGroup(self.mainWindowHandler)




    def installFakeIOFunctions(self, obj=None):
        """
        Replaces the load and save functions in gui.io with fake ones that
        just store the parameters they have been called with. load returns
        obj.
        """
        self.oldLoad = gui.io.load
        self.oldSave = gui.io.save

        def newLoad(*p):
            self.loadParameters = p
            return obj
        def newSave(*p):
            self.saveParameters = p

        gui.io.load = newLoad
        gui.io.save = newSave


    def uninstallFakeIOFunctions(self):
        """Restores the real load and save functions in the gui.io module."""
        gui.io.load = self.oldLoad
        gui.io.save = self.oldSave
        self.loadParameters = None
        self.saveParameters = None



