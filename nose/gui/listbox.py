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

import util
import gui.widgets as widgets

from util import gettext


#: The initial size of the :class:`gui.calibration.dialog.ListBox` at left
#: side of the calibration dialog.
listBoxSize = (225, -1)



class ListBoxHandler(object):
    """
    The list box is the widget shown at left side of the calibration dialog,
    which allows the user to chose the element of the dialog that is to be
    shown in its body. This class handles the creation of and the signals
    emitted by that widget.
    """

    # The instance of CalibrationDialog this handler is a child of.
    _parent = None

    # The top-level container of the widgets this class is responsible for.
    _widget = None

    # The gtk.TreeView used as the list box.
    _treeView = None

    # A dictionary that maps the list box's selection paths to the internal
    # names of the widgets that are to be shown when the paths are selected.
    _widgetNameFromPath = None

    # A tuple of tuples that describe the rows of the list box. The first
    # element is the path; the second element is the internal name of the
    # widget that is to be shown when that path is selected, and the third
    # element is the text of the row at that path.
    ROWS = (
        ((0,),   'measurementTable',      gettext('Measurements')),
        ((1,),   'functionWidget',        gettext('Estimation Functions')),
        ((2,),   'chartParentNode',       gettext('Charts')),
        ((2, 0), 'measurementsChart',     gettext('Measurements')),
        ((2, 1), 'temperatureChart',      gettext('Temperature Estimation')),
        ((2, 2), 'currentChart',          gettext('Current Estimation')),
        ((3,),   'calibrationParentNode', gettext('Calibration')),
        ((3, 0), 'parameterWidget',       gettext('Parameters')),
        ((3, 1), 'progressWidget',        gettext('Progress')))


    def __init__(self, parent):
        """
        Creates a new instance of this class. The parameter parent is the
        instance of CalibrationDialog this handler is a child of.
        """
        self._parent = parent
        self._widgetNameFromPath = {}
        self._createWidgets()


    ###########################################################################
    # WIDGET CREATION                                                         #
    ###########################################################################

    def _createWidgets(self):
        """
        Creates the widget this class is responsible for.
        """
        store = gtk.TreeStore(str)

        for row in self.ROWS:
            self._addRow(store, *row)

        renderer = gtk.CellRendererText()

        column = gtk.TreeViewColumn()
        column.pack_start(renderer, expand=True)
        column.add_attribute(renderer, 'text', 0)

        self._treeView = gtk.TreeView(store)
        self._treeView.append_column(column)
        self._treeView.set_headers_visible(False)
        self._treeView.set_size_request(*listBoxSize)
        self._treeView.expand_all()

        self._treeView.get_selection().select_path((0,))
        self._treeView.get_selection().connect('changed',
            util.WeakMethod(self._selectionChanged))

        self._widget = widgets.createScrolledWindow(self._treeView)
        self._widget.set_shadow_type(gtk.SHADOW_ETCHED_IN)


    def _addRow(self, treeStore, path, widgetName, text):
        """
        Adds a row to the given tree store at the given path, where widgetName
        is the internal name of the widget that is to be shown when that row is
        selected, and text is the text of that row.
        """
        self._widgetNameFromPath[path] = widgetName

        if len(path) > 1:
            parent = treeStore.get_iter(path[0:-1])
        else:
            parent = None

        treeStore.append(parent, [text])


    ###########################################################################
    # SIGNAL HANDLING                                                         #
    ###########################################################################

    def _selectionChanged(self, selection):
        """
        Called when the selection in the list box changes.
        """
        treeModel, rows = selection.get_selected_rows()

        if len(rows) == 0:
            name = 'noSelection'
        elif len(rows) == 1:
            name = self._widgetNameFromPath[rows[0]]
        else:
            assert False, 'somehow, multiple list box rows have been selected'

        self._parent._switchWidget(name)

