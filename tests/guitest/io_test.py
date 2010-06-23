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
import sys
import unittest

import gui.io
import gui.widgets


class AllTests(unittest.TestCase):
    """
    Tests for the gui.io module.
    """

    FNO = os.path.join('tests', 'saves', 'fnord.fno')
    FN2 = os.path.join('tests', 'saves', 'fnord2.fno')
    DEL = os.path.join('tests', 'saves', 'delete.me')
    FER = os.path.join('tests', 'saves', 'not a file')
    PER = os.path.join('tests', 'saves', 'not a directory', 'not a file')


    def setUp(self):
        self.chooser = FakeFileChooserDialog()
        gui.widgets.TESTING_SUPPRESS_REPORTS = True
        gui.io.FILE_TYPES['Fnord'] = (
            'Fnord Files', 'fno', sys.modules[__name__])


    def tearDown(self):
        gui.widgets.TESTING_SUPPRESS_REPORTS = False
        gui.widgets.TESTING_REPORT = None
        gui.widgets.TESTING_REPORT_ID = None
        del gui.io.FILE_TYPES['Fnord']



    def testLoadWithFileName(self):
        """Tests load with a file name."""
        fnord = gui.io.load('Fnord', self.FNO, None, 5, 42)
        self.assertEqual(fnord.fnord, 23)
        self.assertEqual(fnord.fileName, self.FNO)


    def testLoadWithoutFileName(self):
        """Tests load with a file name."""
        self.installFakeChooseFile(self.FNO)
        try:
            fnord = gui.io.load('Fnord', None, None, 5, 42)
            self.assertEqual(fnord.fnord, 23)
            self.assertEqual(fnord.more, (5, 42))
            self.assertEqual(fnord.fileName, self.FNO)
        finally:
            self.uninstallFakeChooseFile()


    def testSaveWithFileName(self):
        """Tests save with a file name."""
        self.assertFalse(os.path.exists(self.FN2))
        try:
            fnord = Fnord(5, 23, 42)
            self.assertTrue(gui.io.save(fnord, 'Fnord', self.FN2))
            self.assertTrue(os.path.exists(self.FN2))
            self.assertEqual(gui.io.read(self.FN2).rstrip(),
                '<fnord>5</fnord>')
            self.assertEqual(fnord.fileName, self.FN2)
        finally:
            os.remove(self.FN2)


    def testSaveWithoutFileName(self):
        """Tests save without a file name."""
        self.assertFalse(os.path.exists(self.FN2))
        self.installFakeChooseFile(self.FN2)
        try:
            self.assertTrue(gui.io.save(Fnord(5, 23, 42), 'Fnord', None))
            self.assertTrue(os.path.exists(self.FN2))
            self.assertEqual(gui.io.read(self.FN2).rstrip(),
                '<fnord>5</fnord>')
        finally:
            os.remove(self.FN2)
            self.uninstallFakeChooseFile()


    def installFakeChooseFile(self, fileName):
        self.oldChooseFile = gui.io.chooseFile
        gui.io.chooseFile = lambda type, mode, parent=None: fileName


    def uninstallFakeChooseFile(self):
        gui.io.chooseFile = self.oldChooseFile
        del self.oldChooseFile


    def testChooseFile(self):
        """Tests chooseFile."""
        oldCreateFileChooser = gui.io._createFileChooser
        oldRunFileChooser = gui.io._runFileChooser

        self.cfca = None
        self.rfca = None
        ffc = object()

        def fakeCreateFileChooser(*p):
            self.cfca = p
            return ffc
        def fakeRunFileChooser(*p):
            self.rfca = p

        try:
            gui.io._createFileChooser = fakeCreateFileChooser
            gui.io._runFileChooser = fakeRunFileChooser

            for type in gui.io.FILE_TYPES.keys():
                for mode in 'rw':
                    gui.io.chooseFile(type, mode)
                    self.assertEqual(self.cfca, (type, mode, None))
                    self.assertEqual(self.rfca, (ffc,))
        finally:
            gui.io._createFileChooser = oldCreateFileChooser
            gui.io._runFileChooser = oldRunFileChooser


    def testChooseFileTesting(self):
        """Tests chooseFile if TESTING_USE_DEFAULT_FILE_NAME is set."""
        gui.io.TESTING_USE_DEFAULT_FILE_NAME = True
        gui.io.TESTING_DEFAULT_FILE_NAME = 'not a real file name'
        try:
            for type in gui.io.FILE_TYPES.keys():
                self.assertEqual(
                    gui.io.chooseFile(type, 'r'), 'not a real file name')
        finally:
            gui.io.TESTING_USE_DEFAULT_FILE_NAME = False
            gui.io.TESTING_DEFAULT_FILE_NAME = None


    def testRead(self):
        """Tests read."""
        self.assertEqual(gui.io.read(self.FNO).rstrip(), '<fnord>23</fnord>')
        self.assertEqual(gui.widgets.TESTING_REPORT_ID, None)


    def testReadWithError(self):
        """Tests reading from a file that does not exist."""
        self.assertEqual(gui.io.read(self.FER), None)
        self.assertEqual(gui.widgets.TESTING_REPORT_ID, 'io')


    def testWrite(self):
        """Tests write."""
        self.assertFalse(os.path.exists(self.DEL))
        try:
            self.assertTrue(gui.io.write('This is a test.', self.DEL))
            self.assertTrue(os.path.exists(self.DEL))
            self.assertEqual(gui.widgets.TESTING_REPORT_ID, None)
        finally:
            os.remove(self.DEL)


    def testWriteWithError(self):
        """Tests writing in a directory that does not exits."""
        self.assertFalse(gui.io.write('This should not work.', self.PER))
        self.assertEqual(gui.widgets.TESTING_REPORT_ID, 'io')


    def testStripPath(self):
        """Tests stripPath."""
        for path in (('foo', 'bar', 'baz.qux'), ('foo.bar')):
            self.assertEqual(gui.io.stripPath(os.path.join(*path)), path[-1])


    def testCreateFileChooser(self):
        """Test _createFileChooser."""
        for type in gui.io.FILE_TYPES:
            for mode in ('r', 'w'):
                chooser = gui.io._createFileChooser(type, mode, None)

                if mode == 'r':
                    expectedAction = gtk.FILE_CHOOSER_ACTION_OPEN
                else:
                    expectedAction = gtk.FILE_CHOOSER_ACTION_SAVE

                self.assertEqual(chooser.get_action(), expectedAction)
                self.assertTrue(chooser.get_do_overwrite_confirmation())


    def testRunFileChooserAbort(self):
        """Tests _runFileChooser; has the user abort the selection."""
        self.chooser.response = gtk.RESPONSE_CANCEL
        self.assertEqual(gui.io._runFileChooser(self.chooser), None)
        self.assertTrue(self.chooser.destroyCalled)


    def testRunFileChooser(self):
        """Tests _runFileChooser; has the user choose a file"""
        self.chooser.fileName = self.FNO
        self.assertEqual(gui.io._runFileChooser(self.chooser), self.FNO)
        self.assertTrue(self.chooser.destroyCalled)


    def testAddFileFilters(self):
        """Test _addFileFilters."""
        for type in gui.io.FILE_TYPES.keys():
            name, ext, module = gui.io.FILE_TYPES[type]

            chooser = gtk.FileChooserDialog()
            gui.io._addFileFilters(chooser, type)

            setFilter = chooser.get_filter()
            allFilters = chooser.list_filters()

            self.assertEqual(len(allFilters), 2)
            self.assertEqual(allFilters[1], setFilter)

            self.assertEqual(setFilter.get_name(), '%s (*.%s)' % (name, ext))
            self.assertTrue(setFilter.filter((None, None, 'foo.' + ext, None)))
            self.assertFalse(setFilter.filter((None, None, 'foo.xxx', None)))

            self.assertTrue(
                allFilters[0].filter((None, None, 'foo.' + ext, None)))
            self.assertTrue(
                allFilters[0].filter((None, None, 'foo.xxx', None)))



class FakeFileChooserDialog(object):
    def __init__(self):
        self.response = gtk.RESPONSE_OK
        self.destroyCalled = False
        self.fileName = 'foo.bar'

    def run(self):
        return self.response

    def get_filename(self):
        if isinstance(self.fileName, list):
            fileName = self.fileName[0]
            self.fileName = self.fileName[1:]
            return fileName
        else:
            return self.fileName

    def destroy(self):
        self.destroyCalled = True


class Fnord(object):
    def __init__(self, fnord, more, evenMore):
        self.fileName = None
        self.fnord = fnord
        self.more = (more, evenMore)


def toXML(fnord):
    return '<fnord>%s</fnord>' % fnord.fnord

def fromXML(text, more, evenMore):
    fnord = int(text[7:-8])
    return Fnord(fnord, more, evenMore)




