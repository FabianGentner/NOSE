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
This package contains a simple chart-drawing library for GTK, which provides
the following features:

* multiple graphs on a single chart

* graphs drawn as continuous lines (*function graphs*) or a series of points
  (*point graphs*)

* ticks and tick labels whose intervals are automatically chosen based on
  an axis' length and maximum value

* *dimension labels* on the axes, which show the dimension of the values on
  that axis, optionally as a proper fraction

* *secondary ordinates*, which are shown on the right side of the charts and
  allow a single chart to show graphs using two different dimensions

* chart captions, which are omitted for charts without graphs

The package contains three modules: :mod:`gui.charting.chart`,
:mod:`gui.charting.axis`, and :mod:`gui.charting.graph`.

A simple GUI using a :class:`~gui.charting.chart.Chart` might be constructed
as follows::

    import gtk
    from gui.charting.chart import Chart
    from gui.charting.graph import FunctionGraph, PointGraph

    function = lambda l: (l / 33)**2
    points = ((0, 2), (20, 5), (40, 3), (60, 12), (80, 15), (100, 22))

    chart = Chart()

    chart.minCaptionLines = 2
    chart.showSecondaryOrdinate = True

    chart.abscissa.maxValue = 100
    chart.ordinate.maxValue = 10
    chart.secondaryOrdinate.maxValue = 25

    chart.abscissa.dimensionLabelText = '<i>l</i> / m'
    chart.ordinate.dimensionLabelText = '<i>t</i> / s'
    chart.secondaryOrdinate.dimensionLabelText = '<i>A</i> / m<sup>2</sup>'

    chart.addGraph(FunctionGraph(function, 'red'))
    chart.addSecondaryGraph(PointGraph(points, 'blue', style='diamonds'))

    chart.captionText = (
        'Shown are some nonsense data (red curve) '
        'and some more nonsense data (blue diamonds).')

    window = gtk.Window()
    window.set_default_size(600, 500)
    window.connect('destroy', lambda widget: gtk.main_quit())
    window.add(chart)
    window.show_all()

    gtk.main()

The resulting chart looks like this:

.. image:: samplechart.png
    :align: center
"""
