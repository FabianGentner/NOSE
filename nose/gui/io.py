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
Contains a number of utility functions related to file input/output.
Does not contain any functions related to any daughter of Inachus,
moon, genus of freshwater snail, band, or editor from *Solstice*,
although the latter would be awesome.
"""

import gtk
import os.path

import gui.widgets as widgets
import ops.calibration.data

from util import gettext


#: A dictionary containing information about the file types used by *NOSE*.
#: Keys are internal names for different types of files (which will not be
#: displayed to the user). The associated values are tupels containing a
#: human-readable description of the file type, the type’s extension, and
#: the module that contains the ``toXML()`` and ``fromXML()`` functions
#: used for the objects saved in files of that type.
FILE_TYPES = {
    'CalibrationData': ('Calibration Data Files', 'cal', ops.calibration.data)}


###############################################################################
# HIGH-LEVEL FUNCTIONS                                                        #
###############################################################################

def load(type, fileName=None, parent=None, *parserParameters):
    """
    Loads an object of the given type from a file. ``type`` must be one of the
    file types listed in :data:`FILE_TYPES`. ``fileName`` must be either the
    name of the file the object that is to be loaded is saved in, or ``None``,
    in which case the user is queried for a file name. ``parent`` is used as
    the *transient parent* of any windows that are shown during loading. Any
    extra arguments are passed to the ``fromXML()`` function for ``type``.

    If the object has a ``fileName`` attribute, it is set to the file name
    the object was loaded from.

    If the user decline to choose a file, or if an error occurs while reading
    or parsing the file, this function returns ``None``. In the case of an
    error, an error message is shown to the user.
    """
    if fileName is None:
        fileName = chooseFile(type, 'r', parent)

    if fileName is None:
        return None

    text = read(fileName, parent)

    if text is None:
        return None

    obj = getattr(FILE_TYPES[type][2], 'fromXML')(text, *parserParameters)

    if obj is None:
        message = PARSE_ERROR_MESSAGE % stripPath(fileName)
        widgets.reportError(parent, message, None, 'parse')
        return None

    if hasattr(obj, 'fileName'):
        obj.fileName = fileName

    return obj


def save(obj, type, fileName=None, parent=None):
    """
    Saves an object of the given type to a file. ``type`` must be one of the
    file types listed in :data:`FILE_TYPES`. ``fileName`` must be either the
    name of athe file the object is to be saved in, or ``None``, in which case
    the user is queried for a file name. ``parent`` is used as the *transient
    parent* of any windows that are shown during loading.

    The function returns ``True`` if the object has been successfully saved.
    If the user declines to choose a file, or if an error occurs while writing
    to the file, it returns ``False``. In the case of an error, an error
    message is shown to the user.

    If the object has a ``fileName`` attribute, it is set to the file name the
    object was saved to.
    """
    if fileName is None:
        fileName = chooseFile(type, 'w', parent)

    if fileName is None:
        return False

    if hasattr(obj, 'fileName'):
        obj.fileName = fileName

    return write(getattr(FILE_TYPES[type][2], 'toXML')(obj), fileName, parent)


###############################################################################
# MID-LEVEL FUNCTIONS                                                         #
###############################################################################

def chooseFile(type, mode, parent=None):
    """
    Displays a dialog that allows the user to choose a file. ``type`` must
    be one of the file types listed in :data:`FILE_TYPES` and is used to
    filter the files that are presented to the user (which does not stop
    the user from selecting a file of another type, though). mode must be
    either ``'r'`` for reading or ``'w'`` for writing. ``parent`` is used
    as the *transient parent* of all windows that are displayed.

    The function returns either the name of the file the user selected,
    or ``None`` if the user cancels the file selection procedure.
    """
    assert mode == 'r' or mode == 'w'

    if TESTING_USE_DEFAULT_FILE_NAME:
        return TESTING_DEFAULT_FILE_NAME
    else:
        return _runFileChooser(_createFileChooser(type, mode, parent))


def read(fileName, parent=None):
    """
    Returns the contents of the file indicated by ``fileName`` as a string.
    If an error occurs while reading the file, it is reported to the user,
    using ``parent`` as the *transient parent* of the error dialog, and
    this function returns ``None``.
    """
    try:
        inFile = open(fileName, 'r')
        text = inFile.read()
        inFile.close()
        return text
    except IOError, e:
        message = READ_ERROR_MESSAGE % stripPath(fileName)
        widgets.reportError(parent, message, e, 'io')
        return None


def write(text, fileName, parent=None):
    """
    Writes text to the file indicated by ``fileName``. If an error occurs
    while writing to the file, it is reported to the user, using ``parent``
    as the *transient parent* of the error dialog. The function returns
    ``True`` if the text has been successfully saved.
    """
    try:
        outFile = open(fileName, 'w')
        outFile.write(text)
        outFile.close()
        return True
    except IOError, e:
        widgets.reportError(parent, WRITE_ERROR_MESSAGE, e, 'io')
        return False


def stripPath(fileName):
    """
    Returns the last component of fileName.

    >>> stripPath('foo/bar/baz.qux')
    'baz.qux'
    """
    return os.path.split(fileName)[1]


###############################################################################
# LOW-LEVEL FUNCTIONS                                                         #
###############################################################################

def _createFileChooser(type, mode, parent):
    """
    Creates a :class:`gtk.FileChooserDialog` that has the user choose
    a file of the given type (which must be one of the file types listed
    in :data:`FILE_TYPES`) for either reading (if ``mode`` is ``'r'``)
    or writing (if ``mode`` is ``'w'``). ``parent`` is used as the transient
    parent of the dialog.
    """
    buttons = [gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, None, gtk.RESPONSE_OK]

    if mode == 'r':
        buttons[2] = gtk.STOCK_OPEN
        action = gtk.FILE_CHOOSER_ACTION_OPEN
    if mode == 'w':
        buttons[2] = gtk.STOCK_SAVE
        action = gtk.FILE_CHOOSER_ACTION_SAVE

    chooser = gtk.FileChooserDialog(None, parent, action, tuple(buttons))
    chooser.set_do_overwrite_confirmation(True)
    _addFileFilters(chooser, type)

    return chooser


def _runFileChooser(chooser):
    """
    Calls the ``run()`` method of the given :class:`gtk.FileChooserDialog`
    and returns the name of the file the user chose.
    """
    if chooser.run() == gtk.RESPONSE_OK:
        fileName = chooser.get_filename()
    else:
        fileName = None

    chooser.destroy()
    return fileName


def _addFileFilters(chooser, type):
    """
    Creates two :class:`gtk.FileFilters` -- one that matches all files,
    and one that matches a known type of files -- and adds them to the given
    :class:`gtk.FileChooserDialog`. ``type`` must be one of the file types
    listed in :data:`FILE_TYPES`, where this function looks up a human-readable
    description for that type of file and its extension.
    """
    name, extension, module = FILE_TYPES[type]
    pattern = '*.' + extension

    filterAll = gtk.FileFilter()
    filterAll.set_name(gettext('All Files'))
    filterAll.add_pattern('*')
    chooser.add_filter(filterAll)

    filterMatching = gtk.FileFilter()
    filterMatching.set_name('%s (%s)' % (name, pattern))
    filterMatching.add_pattern(pattern)
    chooser.add_filter(filterMatching)
    chooser.set_filter(filterMatching)


###############################################################################
# TESTING                                                                     #
###############################################################################

# If :data:`TESTING_USE_DEFAULT_FILE_NAME` is set to ``True``,
# :func:`chooseFile` returns :data:`TESTING_DEFAULT_FILE_NAME`
# rather than asking the user to choose a file. Intended for
# unit testing.
TESTING_USE_DEFAULT_FILE_NAME = False
TESTING_DEFAULT_FILE_NAME = None


###############################################################################
# ERROR MESSAGES                                                              #
###############################################################################

#: The message shown when an error occurs while reading from a file.
READ_ERROR_MESSAGE = gettext('The file "%s" could not be loaded.')

#: The message shown when an error occurs while writing to a file.
WRITE_ERROR_MESSAGE = gettext('There was an error saving the file.')

#: The message shown when an error occurs while parsing a file.
PARSE_ERROR_MESSAGE = gettext(
    'The file "%s" does not have the expected format.')

