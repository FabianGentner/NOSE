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
Contains a number of assorted utility functions used by the application.
"""

# TODO: Add referrence to GUI-related utility functions.

import gettext as gettextmodule
import math
import os
import weakref


###############################################################################
# STRING FORMATTING                                                           #
###############################################################################

def stringFromFloat(n, fractionalDigits=2, trimTrailingZeros=False):
    """
    Returns a string that shows `n` with `fractionalDigits` fractional digits,
    optionally with any trailing zeros removed. If the string would end with
    a ``.``, that is removed as well.

    >>> stringFromFloat(1.001, 2, True)
    '1'
    >>> stringFromFloat(1.001, 2, False)
    '1.00'
    >>> stringFromFloat(1.101, 2, True)
    '1.1'
    >>> stringFromFloat(1.101, 2, False)
    '1.10'
    """
    # str(round(n, fractionDigits)) trims trailing zeros not immediately
    # preceded by the decimal point, so we use string formatting. Please
    # note that the format string itself is created using string formatting
    # in order to insert the desired number of fractional digits.
    string = ('%%.%df' % fractionalDigits) % abs(n)
    if trimTrailingZeros and fractionalDigits > 0:
        string = string.rstrip('0').rstrip('.')
    if n < 0.0:
        string = u'\u2212' + string   # Use a proper minus sign.
    return string

    # TODO: Document new minus.


def stringFromTimePeriod(seconds):
    """
    Returns a string that expresses a period of `seconds` seconds in the form
    :samp:`"{H} hours, {M} minutes, {S} seconds"`, or a localized equivalent,
    with unneeded elements omitted and correct pluralization. Fractions of a
    second are rounded up.

    >>> stringFromTimePeriod(83)
    '1 minute, 23 seconds'
    """
    if seconds < 0:
        raise ValueError('seconds < 0')

    seconds = math.ceil(seconds)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)

    h = m = s = ''
    template = gettext('%d %s')

    if hours > 0:
        h = template % (hours, ngettext('hour', 'hours', hours))
    if minutes > 0:
        m = template % (minutes, ngettext('minute', 'minutes', minutes))
    if seconds > 0:
        s = template % (seconds, ngettext('second', 'seconds', seconds))

    if h or m or s:
        return gettext(', ').join(part for part in (h, m, s) if part)
    else:
        return template % (0, ngettext('second', 'seconds', 0))


###############################################################################
# MATH                                                                        #
###############################################################################

def limit(value, minValue, maxValue):
    """
    Returns the value in the interval [`minValue`, `maxValue`] that is closest
    to `value`. ``None`` may be passed for `minValue` or `maxValue` to signify
    negative infinity and positive infinty, respectively.

    >>> limit(0.5, 0.0, 1.0)
    0.5
    >>> limit(-0.2, 0.0, 1.0)
    0.0
    >>> limit(1.5, 0.0, 1.0)
    1.0
    >>> limit(1.5, 0.0, None)
    1.5
    """
    if minValue is not None and maxValue is not None and minValue > maxValue:
        raise ValueError('minValue > maxValue')
    if minValue is not None and value < minValue:
        return minValue
    if maxValue is not None and value > maxValue:
        return maxValue
    if True:
        return value


def roundToMultiple(n, m):
    """
    Returns the multiple of `m` that is closest to `n`. If two multiples are
    equally close, the function rounds away from zero. If both arguments are
    integers, the return value is an integer as well.

    >>> roundToMultiple(28, 6)
    30
    """
    if isinstance(n, int) and isinstance(m, int):
        return int(round(n / float(m)) * m)
    else:
        return round(n / float(m)) * m


###############################################################################
# WEAK REFERNCES                                                              #
###############################################################################

class WeakMethod(object):
    """
    A weak reference to an instance method. Keeping a reference to
    ``WeakMethod(object.method)`` does not prevent ``object`` from
    being reclaimed as garbage.

    When a :class:`WeakMethod` is called, it forwards the call to
    the method it wraps if the object it is bound to is still alive.
    Otherwise, it raises a :exc:`ReferenceError`::

        >>> class Object(object):
        ...     def method(self):
        ...         return 'Success!'
        ...
        >>> o = Object()
        >>> weakMethod = WeakMethod(o.method)
        >>> weakMethod()
        'Success!'
        >>> o = None
        >>> weakMethod()
        Traceback (most recent call last):
            ...
        ReferenceError: weakly-referenced object no longer exists

    If `callback` is given, it will be called when the object the method
    is bound to is about to be finalized, using the :class:`WeakMethod`
    instance as the only parameter, but calling the :class:`WeakMethod`
    at that point will raise a :exc:`RefernceError`.

    This class does *not* duplicate functionality already provided by
    :func:`weakref.proxy`. An :class:`instancemethod` referenced only
    by a regular weak reference can be reclaimed even if the object
    it is bound to is still alive::

        >>> import weakref
        >>> class Object(object):
        ...     def method(self):
        ...         return 'Success!'
        ...
        >>> o = Object()
        >>> proxy = weakref.proxy(o.method)
        >>> proxy()
        Traceback (most recent call last):
            ...
        ReferenceError: weakly-referenced object no longer exists
    """
    def __init__(self, method, callback=None):
        self._object = weakref.ref(method.__self__, self._noteFinalization)
        self._method = method.__func__
        self._callback = callback


    def __call__(self, *parameters):
        """
        Calls the method, or raises a :exc:`ReferenceError` if the object
        it is bound to has already been reclaimed as garbage.
        """
        o = self._object()
        if o:
            return self._method(o, *parameters)
        else:
            raise ReferenceError('weakly-referenced object no longer exists')


    def _noteFinalization(self, reference):
        """
        Called when the the object the method is bound to is about to be
        finalized. Calls :attr:`_callback`.
        """
        if self._callback:
            self._callback(self)


    def isSameMethod(self, method):
        """
        Indicates whether `method` is the same method, bound to the same
        object, as the method wrapped by the instance.
        """
        sameObject = self._object() is method.__self__
        sameMethod = self._method == method.__func__
        return sameObject and sameMethod


###############################################################################
# INTERNATIONALIZATION                                                        #
###############################################################################

# The :mod:`gettext` translations class used for localization.
# See the documentation of the :mod:`gettext` module for details.
# Used by :func:`gettext` and :func:`ngettext`.
# THIS IS A NON-EXTRACTABLE COMMENT.
TRANSLATIONS = gettextmodule.translation(
    domain='nose',
    localedir=os.path.join('resources', 'messages'),
    fallback=True,
    languages=['en, de'])


# NOTE: The names of the following two functions are magical. Renaming them
#       will break the extraction of translatable strings.


def gettext(string):
    """
    Returns the localized equivalent of `string`, using :data:`TRANSLATIONS`.

    .. note::

        In order for the automatic extraction of translatable strings to work,
        `string` must be a string literal: ``gettext('foo')`` can be extracted;
        ``foo = 'foo'``, ``gettext(foo)`` cannot.

    See the documentation of the :mod:`gettext` module for details.
    """
    return TRANSLATIONS.gettext(string)


def ngettext(singular, plural, number):
    """
    Returns the localized equivalent of what is expressed using `singular`
    or `plural` in English, pluralized according to `number`, and using
    :data:`TRANSLATIONS`. ::

        text = ngettext('bar', 'bars', barCount)

    is *not* simply a more convenient way for writing ::

        if barCount == 1:
            text = gettext('bar')
        else:
            text = gettext('bars')

    since the target language may have more complex pluralization rules.

    .. note::

        In order for the automatic extraction of translatable strings to work,
        `singular` and `plural` must be a string literals:
        ``ngettext('bar', 'bars', barCount)`` can be extracted;
        ``bar, bars = 'bar', 'bars'``, ``ngettext(bar, bars, barCount)``
        cannot.

    See the documentation of the :mod:`gettext` module for details.
    """
    return TRANSLATIONS.ngettext(singular, plural, number)



def parseOrDefault(text, function, default):
    # TODO: Comment
    try:
        return function(text)
    except ValueError:
        return default



###############################################################################
# EXCEPTION CLASSES                                                           #
###############################################################################

class ApplicationError(Exception):
    """
    The base class for all exceptions specific to *NOSE*.
    """
