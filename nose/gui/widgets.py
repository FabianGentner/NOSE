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


#: The application-standard width for borders around panels.
PANEL_BORDER_WIDTH = 12

#: The application-standard width for the spacing between widgets in a panel.
PANEL_SPACING = 12


###############################################################################
# WIDGET CREATION                                                             #
###############################################################################

def createPanel(*children, **keywords):
    """
    Creates a :class:`gtk.Alignment` that contains the given widgets (in a
    :class:`gtk.VBox` if there is more than one widget) and sets the border
    width and spacing between widgets to :data:`PANEL_BORDER_WIDTH` and
    :data:`PANEL_SPACING`, respectively. Any keyword arguments are passed
    to :func:`gtk.Alignment`.
    """
    alignment = gtk.Alignment(**keywords)
    alignment.set_border_width(PANEL_BORDER_WIDTH)

    if len(children) == 1:
        alignment.add(children[0])
    else:
        box = gtk.VBox()
        box.set_spacing(PANEL_SPACING)
        for c in children:
            box.pack_start(c)
        alignment.add(box)

    return alignment


def createCellDataRounder(index, fractionalDigits=2, trimTrailingZeros=False):
    """
    Returns a *cell data function* for use in a :class:`gtk.TreeViewColumn`
    that shows rounded floating-point numbers. The function retrieves its
    data from column `index` of the :class:`gtk.TreeModel` used by the
    :class:`gtk.TreeView` the :class:`gtk.TreeViewColumn` is part of.
    The retrieved number is then rounded using :func:`util.stringFromFloat`,
    which is called with `fractionalDigits` and `trimTrailingZeros` as
    arguments.
    """
    def cellDataRounder(column, renderer, model, iterator):
        value = model.get_value(iterator, index)
        text = util.stringFromFloat(value, fractionalDigits, trimTrailingZeros)
        renderer.set_property('text', text)
    return cellDataRounder


def addMenuItem(menu, text, stock, callback, *parameters):
    """
    Adds a :class:`gtk.ImageMenuItem` to the given :class:`gtk.Menu` using
    the given text and the icon from the given stock. Also adds `callback`
    to the handlers for the menu item's `activate` signal with the given
    extra parameters.
    """
    item = gtk.ImageMenuItem(stock)
    item.get_child().set_text_with_mnemonic(text)
    item.connect('activate', callback, *parameters)
    menu.add(item)
    return item



###############################################################################
# UTILIT FUNCTIONS                                                            #
###############################################################################

def getColor(spec):
    """
    Given a color specification which may be either an X11 color name
    (:samp:`'misty rose'`) or a hexadecimal string (:samp:`'#FFE4E1'`),
    returns a :class:`gtk.gdk.Color` object matching that specification.

    `spec` may also be a :class:`gtk.gdk.Color` object, in which case it
    is returned.
    """
    if isinstance(spec, gtk.gdk.Color):
        return spec
    else:
        return gtk.gdk.colormap_get_system().alloc_color(spec, False, True)










###############################################################################




LABEL_WIDGET_SPACING = 36
RADIO_DEPENDENT_INDENT = 36
RADIO_TO_DEPENDENTS_SPACING = 3
INTER_RADIO_SPACING_COMPLICATED = 6


def alignLeft(widget):
    alignment = gtk.Alignment()
    alignment.add(widget)
    return alignment


def alignLeftCenter(widget):
    alignment = gtk.Alignment(yalign=0.5)
    alignment.add(widget)
    return alignment

def alignLeftCenterFill(widget):
    alignment = gtk.Alignment(yalign=0.5, yscale=1.0)
    alignment.add(widget)
    return alignment




#: TODO
ALIGN = { 'center': 0.5, 'left': 0.0, 'right': 1.0, 'fill': 0.0 }

#: TODO
SCALE = { 'center': 0.0, 'left': 0.0, 'right': 0.0, 'fill': 1.0 }


# FIXME: Use regular constants.

#: A dictionary that contains application-standard widths for different
#: kinds of spacing. Legal keys are ``'none'``, ``'narrow'``, ``'medium'``,
#: ``'wide'``, ``'wider'``, and ``'extra'``
SPACING = {'none': 0, 'narrow': 3, 'medium': 6, 'wide': 12,
    'wider': 24, 'extra': 36 }

#: The application-standard width of :class:`gtk.Entry` instances that are
#: used to enter numbers.
NUMBER_ENTRY_WIDTH = 7


###############################################################################
# WIDGET CREATION                                                             #
###############################################################################



def createButtonBox(*buttons):
    """
    Creates and returns a :class:`gtk.HButtonBox` that contains the given
    buttons and uses application-standard alignment and spacing.
    """
    buttonBox = gtk.HButtonBox()
    buttonBox.set_layout(gtk.BUTTONBOX_END)
    buttonBox.set_homogeneous(True)
    buttonBox.set_border_width(PANEL_BORDER_WIDTH)
    buttonBox.set_spacing(SPACING['wide'])
    for b in buttons:
        buttonBox.pack_end(b)
    return buttonBox


def createScrolledWindow(widget):
    """
    Creates and returns a :class:`gtk.ScrolledWindow` that contains `widget`
    and has its horizontal and vertical scrolling policies set to
    :attr:`gtk.POLICY_AUTOMATIC`.
    """
    scrolledWindow = gtk.ScrolledWindow()
    scrolledWindow.add(widget)
    scrolledWindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    return scrolledWindow


def createNumberEntry(default=''):
    """
    Creates and returns a :class:`gtk.Entry` that has the application-standard
    width and alignment for entries that are used to enter numbers. Does *not*
    ensure that the text entered into the entry is a valid number.
    """
    # TODO: Might want to ensure that the input is numeric.
    entry = gtk.Entry()
    entry.set_width_chars(NUMBER_ENTRY_WIDTH)
    entry.set_text(str(default))
    entry.set_alignment(1.0)
    return entry


def createNumberEntryWithUnit(unit, default=''):
    """
    Creates a :class:`gtk.Entry` that has the application-standard width and
    alignment for entries that are used to enter numbers and is followed by a
    label that shows the given unit, then returns the entry and a
    :class:`gtk.HBox` that contains both entry and unit lable. Does *not*
    ensure that the text entered into the entry is a valid number.
    """
    entry = createNumberEntry(default)
    return entry, createUnitBox(entry, unit)


def createUnitBox(widget, unit):
    """
    Creates and returns a :class:`gtk.HBox` that contains `widget` followed
    by a label that shows the given unit.
    """
    box = gtk.HBox()
    box.set_spacing(SPACING['narrow'])
    box.pack_start(widget, expand=False)
    box.pack_start(gtk.Label(unit), expand=False)
    return box


def createMnemonicLabel(widget, text):
    label = gtk.Label(text)
    # ISSUE: yalign 0.5 is exactly right for labels for entries, but won't
    #        work for taller widgets.
    label.set_alignment(0.0, 0.5)
    label.set_use_underline(True)
    label.set_mnemonic_widget(widget)
    return label


def createHalfStockButton(stock, labelText):
    """
    Creates and returns a button with the given label text and the icon from
    the given stock item. This is more tricky than it sounds.
    """
    button = gtk.Button(stock=stock)
    label = button.get_children()[0].get_children()[0].get_children()[1]
    label.set_text(labelText)
    label.set_use_underline(True)
    return button


def createProgressBarWithLabel():
    progressBar = gtk.ProgressBar()
    label = gtk.Label()
    label.set_alignment(0.0, 0.0)
    box = gtk.VBox()
    box.set_spacing(SPACING['narrow'])
    box.pack_start(progressBar)
    box.pack_start(label)
    return progressBar, label, box






###############################################################################
# THE ENTRY TABLE BUILDER CLASS                                               #
###############################################################################

# FIXME: Not used. Delete?

class EntryTableBuilder(object):
    """
    Creates a new *entry table builder*.

    An *entry table* is a :class:`gtk.Table` that has two columns, where the
    right one contains a number of :class:`gtk.Entry` instances, and the left
    one contains labels that identify these entries and optionally provide a
    mnemonic for selecting them.

    This class simplifies the process of creating such a table by providing
    a convenience method (:meth:`addNumberEntry`) that creates the label and
    entry, and sets up the shortcut. The actual :class:`gtk.Table` can then
    be created by calling :meth:`buildTable`.
    """

    def __init__(self):
        self._labels = []
        self._payload = []
        self._hasFullWidthElements = False


    def addFullWidthWidget(self, widget):
        self._labels.append(None)
        self._payload.append(widget)
        self._hasFullWidthElements = True


    def addNumberEntry(self, labelText, unit=None, default=''):
        """
        Creates a :class:`gtk.Entry` that has the application-standard width
        and alignment for entries that are used to enter numbers (and is
        optionally followed by a label that shows the given unit) and a
        label with the given text, then adds them to the table and returns
        the entry. Does *not* ensure that the text entered into the entry is
        a valid number.
        """
        entry = createNumberEntry(default)
        self.addWidget(labelText, entry, unit)
        return entry


    def addWidget(self, labelText, widget, unit=None):
        """
        Creates a label with the given text, and adds it and the given widget
        (optionally followd by a label that shows the given unit) to the table.
        """
        label = gtk.Label(labelText)
        # ISSUE: yalign 0.5 is exactly right for labels for entries, but won't
        #        work for taller widgets.
        label.set_alignment(0.0, 0.5)
        label.set_use_underline(True)
        label.set_mnemonic_widget(widget)

        self._labels.append(label)

        if unit == None:
            self._payload.append(widget)
        else:
            self._payload.append(createUnitBox(widget, unit))


    def buildTable(self):
        """
        Creates and returns a :class:`gtk.Table` that uses the widgets added
        to the :class:`EntryTableBuilder` using the various :meth:`add...`
        methods. This method may only be called once on each instance.
        """
        table = gtk.Table(rows=len(self._labels), columns=2)
        table.set_col_spacing(0, SPACING['extra'])

        for r, (label, widget) in enumerate(zip(self._labels, self._payload)):
            align = gtk.Alignment(0.0, 0.0, 0.0, 0.0)
            align.add(widget)

            if label == None:
                table.attach(align, 0, 2, r, r + 1, xoptions=gtk.FILL)
            else:
                if self._hasFullWidthElements:
                    labelAlign = gtk.Alignment(yalign=0.5)
                    labelAlign.set_padding(0, 0, SPACING['wider'], 0)
                    labelAlign.add(label)
                    label = labelAlign

                table.attach(label, 0, 1, r, r + 1, xoptions=gtk.FILL)
                table.attach(align, 1, 2, r, r + 1, xoptions=gtk.FILL)
        return table


###############################################################################
# ERROR MESSAGES AND QUERIES                                                  #
###############################################################################

#: If set to ``True``, :func:`reportError` does not actually report errors.
#: Instead, if :data:`TESTING_REPORT` and :data:`TESTING_REPORT_ID` are both
#: ``None``, it sets them to the error message and id. Oterwise, it raises
#: an :exc:`AssertionError`.
TESTING_SUPPRESS_REPORTS = False

#: Set to the error message when :func:`reportError` is called and
#: :data:`TESTING_SUPPRESS_REPORTS` is ``True``.
TESTING_REPORT = None

#: Set to the error id when :func:`reportError` is called and
#: :data:`TESTING_SUPPRESS_REPORTS` is ``True``.
TESTING_REPORT_ID = None


#: If set to a value other than ``None``, :func:`askUser` does not actually
#: query the user. Instead, if :data:`TESTING_QUESTION_ASKED` is ``False``,
#: it sets it to ``True`` and returns the value of this attribute. Otherwise
#: it raises an :exc:`AssertionError`.
TESTING_DEFAULT_ANSWER = None

#: Set to ``True`` when :func:`askUser` is called and
#: :data:`TESTING_DEFAULT_ANSWER` is not ``None``.
TESTING_QUESTION_ASKED = False


def reportError(widget, message, exception, id=None):
    if TESTING_SUPPRESS_REPORTS:
        global TESTING_REPORT, TESTING_REPORT_ID
        assert TESTING_REPORT == None and TESTING_REPORT_ID == None
        TESTING_REPORT = message
        TESTING_REPORT_ID = id
    else:
        dialog = gtk.MessageDialog(
            parent=getToplevelWindow(widget),
            type=gtk.MESSAGE_ERROR,
            buttons=gtk.BUTTONS_OK,
            message_format=message)

        dialog.run()
        dialog.destroy()


def askUser(widget, question, title=''):
    if TESTING_DEFAULT_ANSWER is not None:
        global TESTING_QUESTION_ASKED
        assert not TESTING_QUESTION_ASKED
        TESTING_QUESTION_ASKED = True
        return TESTING_DEFAULT_ANSWER
    else:
        dialog = gtk.MessageDialog(
            parent=getToplevelWindow(widget),
            type=gtk.MESSAGE_QUESTION,
            buttons=gtk.BUTTONS_YES_NO,
            message_format=question)

        dialog.set_title(title)
        response = dialog.run()
        dialog.destroy()

        return response == gtk.RESPONSE_YES


###############################################################################
# UTILITY FUNCTIONS                                                           #
###############################################################################

# FIXME: Double-check.

def isInWindow(widget):
    return getToplevelWindow(widget) != None


def getToplevelWindow(widget):
    toplevel = widget.get_toplevel()
    if toplevel.flags() & gtk.TOPLEVEL:
        return toplevel
    else:
        return None


def arrangeDefaulting(defaultWidget, *entries):
    for e in entries:
        e.set_activates_default(True)
    defaultWidget.set_flags(gtk.CAN_DEFAULT)
    defaultWidget.grab_default()


