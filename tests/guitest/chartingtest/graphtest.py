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
import unittest

from test import *
from gui.charting.graph import *

import gui.charting.chart


class GraphTests(unittest.TestCase):
    """
    Tests for the :mod:`gui.charting.graph` module.
    """

    def setUp(self):
        self.chart = gui.charting.chart.Chart()

        self.functionGraph = FunctionGraph(
            lambda x: 2 * x * x, 'pink', drawOnFrame = False)

        x = (-0.2, -0.1, 0.0, 0.0, 0.1, 0.2, 0.5, 0.8,  0.9, 1.0, 1.0, 1.1)
        y = (-0.5,  0.3, 0.0, 0.1, 0.0, 0.2, 1.0, 1.1, -0.1, 0.9, 1.0, 0.7)
        self.pointGraph = PointGraph(zip(x, y), 'violet', style='diamonds')

        self.chart.addGraph(self.functionGraph)
        self.chart.addGraph(self.pointGraph)

        # The chart needs to be realized and have an allocation for some tests.
        window = gtk.Window()
        self.chart.size_allocate((0, 0, 300, 300))
        window.add(self.chart)
        self.chart.realize()


    def testDrawFunctionGraph(self):
        """Tests the :meth:`draw` method of :class:`FunctionGraph`."""
        self.functionGraph.draw(
            self.chart, self.chart.abscissa, self.chart.ordinate)


    def testBadPontGraphStyle(self):
        """Tests creating a :class:`PointGraph` with an invalid style."""
        self.assertRaises(ValueError, PointGraph, ((1, 2), (3, 4)), 'red', 'x')


    def testDrawPointGraph(self):
        """Tests the :meth:`draw` method of :class:`PointGraph`."""
        self.pointGraph.draw(
            self.chart, self.chart.abscissa, self.chart.ordinate)


