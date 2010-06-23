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
This module contains the :class:`ProgressWidgetHandler` class, which manages
a group of widgets that show the progress of the :term:`calibration procedure`
while it is running.

The class listens to :class:`~ops.calibration.event.CalibrationStarted` and
:class:`~ops.calibration.event.CalibrationOver` events to determine whether
the calibration procedure is running. While it is running, it periodically
obtains progress information from the responsible
:class:`~ops.calibration.manager.CalibrationManager`, and uses this information
to update two progress bars that show the estimated progress of the ongoing
:term:`calibration stage` and the calibration procedure as whole, and two
labels that show the estimated time remaining for both.

The top-level container of these widgets can be accessed using the handler's
:attr:`~ProgressWidgetHandler.widget` property. Clients also need to keep a
reference to the handler itself to prevent it from being reclaimed as
garbage, but need not otherwise deal with it.

The :class:`ProgressWidgetHandler` allows clients to register additional
:class:`gtk.ProgressBar` and :class:`gtk.Label` instances, however, which
will then receive periodic progress updates as well.
"""

import gtk

import gui.widgets as widgets
import util

from util import gettext, ngettext
from ops.calibration.event import CalibrationStarted, CalibrationOver
from ops.calibration.manager import *



def getMessage(status, used, unused, calibrated, wasCalibrated):
    """
    """
    if status == STATUS_ABORTED:
        text = gettext('The calibration procedure has been aborted.')
    elif len(used) > 0:
        text = gettext('The calibration procedure has finished')
        if not calibrated:
            text += gettext(
                ', but too few measurements have been taken to fit'
                ' the estimation functions')
        text += gettext('.')
    else:
        text = ''

    text += '\n\n'

    if len(used) == 0:
        text += gettext('No measurements have been taken')
        if status == STATUS_INVALID_CURRENT:
            text += ngettext(
                ' because the current exceeds the system\'s maximum current',
                ' because all currents exceed the system\'s maximum current',
                len(unused))
        elif status == STATUS_SAFE_MODE_TRIGGERED:
            text += gettext(
                ' because the temperature sensor voltage recorded while '
                ' heating with %s exceeds the system\'s safety threshold')
            text = text % ngettext(
                'the current', 'the first current', len(unused))
        elif status == STATUS_FINISHED:
            text += gettext(' because there were no currents to use')
        text += gettext('.')
    else:
        text += ngettext(
            'A measurement has been taken for the current %s mA.',
            'Measurements have been taken for the currents %s mA.',
            len(used))
        text = text % makeList(used)

        if len(unused) > 0:
            text += '\n\n'

            text += ngettext(
                'No measurement has been taken for the current %s mA',
                'No measurements have been taken for the currents %s mA',
                len(unused))
            text = text % makeList(unused)
            if status == STATUS_INVALID_CURRENT:
                text += ngettext(
                    ' because it exceeds the system\'s maximum current',
                    ', because they exceed the system\'s maximum current',
                    len(unused))
            elif status == STATUS_SAFE_MODE_TRIGGERED:
                text += gettext(
                    ' because the temperature sensor voltage recorded while '
                    ' heating with %s exceeds the system\'s safety threshold')
                text = text % ngettext(
                    'that current', 'the first of these currents', len(unused))
            text += gettext('.')

        if calibrated:
            text += '\n\n'
            if wasCalibrated:
                text += gettext('The estimation functions have been updated.')
            else:
                text += gettext('The estimation functions have been fitted.')

    return text.strip()


def makeList(currents):
    si = tuple(util.stringFromFloat(i, 2, True) for i in currents)
    if len(currents) == 1:
        return si[0]
    if len(currents) == 2:
        return si[0] + gettext(' and ') + si[1]
    else:
        return gettext(', ').join(si[:-1]) + gettext(', and ') + si[-1]



###############################################################################
# PROGRESS WIDGET WRAPPER                                                     #
###############################################################################

class ProgressWidgetWrapper(object):

    def __init__(self, system):
        self._progressWidgetHandler = ProgressWidgetHandler(system)
        self._createWidgets()
        self._wasCalibrated = None

        system.mediator.addListener(self._calibrationListener,
            CalibrationStarted, CalibrationOver)

    @property
    def handler(self):
        return self._progressWidgetHandler


    @property
    def widget(self):
        """
        The top-level container of the widgets. Immutable.
        """
        return self._widget


    def _calibrationListener(self, event):
        if event.calibrationIsRunning:
            self.handler.widget.show()
            self._noCalibrationLabel.hide()
            self._wasCalibrated = event.system.isCalibrated
        else:
            self.handler.widget.hide()
            self._noCalibrationLabel.show()
            self._updateNoCalibrationLabel(event)


    def _updateNoCalibrationLabel(self, event):
        message = getMessage(
            event.status,
            event.usedCurrents,
            event.unusedCurrents,
            event.system.isCalibrated,
            self._wasCalibrated)
        self._noCalibrationLabel.set_text(message)


    def _createWidgets(self):
        self.handler.widget.show_all()
        self.handler.widget.hide()
        self.handler.widget.set_no_show_all(True)

        self._noCalibrationLabel = gtk.Label(
            gettext('The production system is not being calibrated.'))
        self._noCalibrationLabel.set_line_wrap(True)
        self._noCalibrationLabel.set_justify(gtk.JUSTIFY_CENTER)
        self._noCalibrationLabel.show()
        self._noCalibrationLabel.set_no_show_all(True)

        # TODO: Use predefined container from widgets?
        self._widget = gtk.HBox()
        self._widget.set_border_width(12)
        self._widget.pack_start(self.handler.widget)
        self._widget.pack_start(self._noCalibrationLabel)
        self._widget.show()





###############################################################################
# PROGRESS WIDGET HANDLER                                                     #
###############################################################################

class ProgressWidgetHandler(object):
    """
    Creates a new instance of this class, which shows the progress of
    calibration procedures performed on the given
    :class:`~ops.system.ProductionSystem`.
    """

    def __init__(self, system):
        self.stageProgressBars = []
        self.totalProgressBars = []
        self.progressLabels = []
        self._calibrationManager = None
        self._createWidgets()

        system.mediator.addListener(self._calibrationListener,
            CalibrationStarted, CalibrationOver)


    @property
    def widget(self):
        """
        The top-level container of the widgets that show the progress.
        Immutable.
        """
        return self._widget


    #: The interval in which the progress widgets are updated, in milliseconds.
    #: This is a class attribute, but it can be set on an instance before the
    #: calibration procedure is started to override the default value.
    updateInterval = 250


    def _calibrationListener(self, event):
        """
        Called when a :class:`~ops.calibration.event.CalibrationStarted` or
        :class:`~ops.calibration.event.CalibrationOver` event is sent.
        Starts or stops the widget's updates.
        """
        if event.calibrationIsRunning:
            self._calibrationManager = event.manager
            event.system.mediator.addTimeout(self.updateInterval, self._update)
        else:
            self._calibrationManager = None


    ###########################################################################
    # REGISTERING ADDITIONAL WIDGETS                                          #
    ###########################################################################

    def addStageProgressBar(self, bar, showText=True):
        """
        Registers the given :class:`gtk.ProgressBar` for periodic updates with
        the progress of the ongoing calibration stage while the calibration
        procedure is running. If `showText` is ``True``, the stage progress in
        percent will also be shown as a string on the progress bar.
        """
        if showText:
            bar.set_text('0%')
        self.stageProgressBars.append((bar, showText))


    def addTotalProgressBar(self, bar, showText=True):
        """
        Registers the given :class:`gtk.ProgressBar` for periodic updates with
        the progress of the entire calibration procedure while it is running.
        If `showText` is ``True``, the total progress in percent will also be
        shown as a string on the progress bar.
        """
        if showText:
            bar.set_text('0%')
        self.totalProgressBars.append((bar, showText))


    def addDefaultStageProgressLabel(self, label):
        """
        A convenience method that calls :meth:`addProgressLabel` with
        a suitable template for a label that is to show the progress of
        the ongoing calibration stage.
        """
        self.addProgressLabel(
            label,
            gettext(u'%(action)s \u2014 %(stageTimeLeft)s remaining'),
            gettext(u'%(action)s'))


    def addDefaultTotalProgressLabel(self, label):
        """
        A convenience method that calls :meth:`addProgressLabel` with
        a suitable template for a label that is to show the calibration
        procedure's total progress.
        """
        self.addProgressLabel(
            label,
            gettext('Total time remaining: %(totalTimeLeft)s'),
            gettext('%(emptyString)s'))


    # TODO: Document gettext gotcha.

    def addProgressLabel(self, label, template, noTimeTemplate):
        """
        Registers the given :class:`gtk.Label` for periodic updates with the
        calibration procedure's progress while it is running. The label's text
        will be set to `template` if the remaining duration of the stage and
        the calibration procedure as a while are known, and to `noTimeTemplate`
        otherwise. The templates may include the following mapping keys:

        ``%(action)s``:
            A localized description of the action that is being performed
            (e.g. ``'Heating with 8 mA'``).
        ``%(stageProgress)s`` and ``%(totalProgress)s``:
            The progress of the ongoing calibration stage and the
            entire calibration procedure, as a string (e.g. ``'23%'``).
        ``%(stageTimeLeft)s`` and ``%(totalTimeLeft)s``:
            The estimated time remaining until the completion of the ongoing
            calibration stage and the entire calibration procedure, as a
            localized string (e.g. ``'3 minutes, 14 seconds'``), or the
            localized equivalent of ``'unknown'`` if the time left is not
            known.
        ``%(emptyString)s``:
            The empty string.
        """
        self.progressLabels.append((label, template, noTimeTemplate))


    ###########################################################################
    # WIDGET CREATION                                                         #
    ###########################################################################

    def _createWidgets(self):
        """
        Creates the widgets this class is responsible for.
        """
        stageBar, stageLabel, stageBox = widgets.createProgressBarWithLabel()
        self.addStageProgressBar(stageBar)
        self.addDefaultStageProgressLabel(stageLabel)

        totalBar, totalLabel, totalBox = widgets.createProgressBarWithLabel()
        self.addTotalProgressBar(totalBar)
        self.addDefaultTotalProgressLabel(totalLabel)

        self._widget = widgets.createPanel(
            stageBox, totalBox, xscale=1.0, yalign=0.5)


    ###########################################################################
    # WIDGET UPDATES                                                          #
    ###########################################################################

    def _update(self):
        """
        Updates the progress widgets with the latest progress information.
        """
        if self._calibrationManager == None:
            return False   # We're done; the timeout can be removed.

        progress = self._calibrationManager.getExtendedProgress()
        stageProgress, stageTimeLeft, totalProgress, totalTimeLeft = progress

        state = self._calibrationManager.state

        if state == STATE_MOVING_HEATER:
            action = gettext('Moving the heater forwards')
        elif state in (STATE_HEATING, STATE_WAITING_FOR_TEMPERATURE):
            current = self._calibrationManager.system.heatingCurrent
            current = util.stringFromFloat(current, 8, True)
            action = gettext('Heating with %s mA') % current
        else:
            assert False

        assert 0.0 <= stageProgress <= 1.0
        assert 0.0 <= totalProgress <= 1.0

        stageProgressText = '%d%%' % (round(stageProgress * 100))
        totalProgressText = '%d%%' % (round(totalProgress * 100))

        for bar, showText in self.stageProgressBars:
            bar.set_fraction(stageProgress)
            if showText:
                bar.set_text(stageProgressText)

        for bar, showText in self.totalProgressBars:
            bar.set_fraction(totalProgress)
            if showText:
                bar.set_text(totalProgressText)

        if stageTimeLeft == None:
            stageTimeLeftText = gettext('unknown')
        else:
            stageTimeLeftText = util.stringFromTimePeriod(stageTimeLeft)

        if totalTimeLeft == None:
            totalTimeLeftText = gettext('unknown')
        else:
            totalTimeLeftText = util.stringFromTimePeriod(totalTimeLeft)

        substitutions = {
            'action':        action,
            'stageProgress': stageProgressText,
            'stageTimeLeft': stageTimeLeftText,
            'totalProgress': totalProgressText,
            'totalTimeLeft': totalTimeLeftText,
            'emptyString':   ''}

        for label, template, noTimeTemplate in self.progressLabels:
            if stageTimeLeft == None or totalTimeLeft == None:
                label.set_text(noTimeTemplate % substitutions)
            else:
                label.set_text(template % substitutions)

        return True   # This method should be called again.

