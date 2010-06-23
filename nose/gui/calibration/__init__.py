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


# FIXME: Outdated
"""
This package consists of a number of modules that contain calibration-related
widgets. The main widget, and the only one clients will normally need to deal
with, is the *calibration dialog*, which is the responsibility of
:class:`gui.calibration.dialog.CalibrationDialogHandler`.

No special setup is necessary to use the calibration dialog as is. Clients need
only instantiate it and call its
:meth:`gui.calibration.dialog.CalibrationDialogHandler.present` method::

    calibrationDialogHandler = CalibrationDialogHandler(system)
    calibrationDialogHandler.present()

If the dialog is closed, it is just hidden, not destroyed. The client can reuse
it by calling :meth:`gui.calibration.dialog.CalibrationDialogHandler.present`
again.

Clients need to keep a reference to the dialog handler alive for as long
as they are using it, however, since it will otherwise be prematurely
reclaimed by the garbage collector.

|

**Components of the Calibration Dialog**

Most of the widgets that make up the calibration dialog are the responsibility
of subordinate handler classes. The right side of the calibration dialog
contains a number of widgets the user can switch between:

* the *measurement table*
  (see :class:`gui.calibration.table.MeasurementTableHandler`),
* the *summary chart*, *temperature chart*, and *current chart*
  (see :class:`gui.calibration.charts.ChartHandler`),
* the *calibration parameter widget*
  (see :class:`gui.calibration.parameters.ParameterWidgetHandler`), and
* the *calibration progress widget*
  (see :class:`gui.calibration.progress.ProgressWidgetHandler`).

At the bottom of the dialog is the *temperature entry widget*
(see :class:`gui.calibration.entry.TemperatureEntryHandler`).


These modules have been designed to be usable independently of the calibration
dialog, so that other configurations are easily possible.
"""

__all__ = [
    'dialog',
    'table'
    'charts',
    'parameters',
    'progress',
    'entry']
