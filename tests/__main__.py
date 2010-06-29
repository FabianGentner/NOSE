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
Runs the application's test suite. To perform the tests, run this module
from the command line.
"""

import gettext
import os
import sys
import unittest

sys.path.append(os.path.join('.', 'nose'))

import util


if __name__ == '__main__':
    # To simplify testing of functions that normally return localized text,
    # :func:`util.gettext` and :func:`util.ngettext` should just return their
    # English arguments during testing.
    util.TRANSLATIONS = gettext.NullTranslations()

    tests = (
        'styletest',
        'utiltest',
        'opstest.simulationtest',
        'opstest.systemtest',
        'opstest.calibrationtest.datatest',
        'opstest.calibrationtest.leastsquaretest',
        'opstest.calibrationtest.managertest',

        'guitest.calibrationtest.tabletest',
        'guitest.calibrationtest.functionstest',
        'guitest.calibrationtest.chartstest',
        'guitest.calibrationtest.parameterstest',
        'guitest.calibrationtest.progresstest',
        'guitest.calibrationtest.entrytest',

        'guitest.chartingtest.charttest',
        'guitest.chartingtest.axistest',
        'guitest.chartingtest.graphtest',

        ## TODO: Rename test modules below this comment.
        ##'gui.main_test',
        ##gui.calibrationtest.dialog_test',

        'guitest.actions_test',
        'guitest.io_test',
    )

    suite = unittest.defaultTestLoader.loadTestsFromNames(tests)
    unittest.TextTestRunner().run(suite)
