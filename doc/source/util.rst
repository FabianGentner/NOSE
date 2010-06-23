:mod:`util` --- Contains assorted utility functions
===================================================

.. automodule:: util

String Formatting
-----------------
.. autofunction:: stringFromFloat
.. autofunction:: stringFromTimePeriod

Math
----
.. autofunction:: limit
.. autofunction:: roundToMultiple

Weak References
---------------
.. autoclass:: WeakMethod
.. automethod:: WeakMethod.isSameMethod

Internationalization
--------------------
..
    WORKAROUND: autodoc does not pick up the docstring for TRANSLATIONS
                for some reason.

.. autodata:: TRANSLATIONS

    The :mod:`gettext` translations class used for localization.
    See the documentation of the :mod:`gettext` module for details.
    Used by :func:`gettext` and :func:`ngettext`.

.. autofunction:: gettext
.. autofunction:: ngettext

Exception Classes
-----------------
.. autoclass:: ApplicationError
