:mod:`gui.widgets` --- Contains GUI-related utility functions
=============================================================

.. automodule:: gui.widgets

Widget Creation
---------------
.. autofunction:: createPanel
.. autofunction:: createCellDataRounder
.. autofunction:: addMenuItem

Utility Functions
-----------------
.. autofunction:: getColor

Constants
---------
.. autodata:: PANEL_BORDER_WIDTH
.. autodata:: PANEL_SPACING

.. comment


    .. autofunction:: createButtonBox
    .. autofunction:: createScrolledWindow
    .. autofunction:: createNumberEntry
    .. autofunction:: createNumberEntryWithUnit
    .. autofunction:: createUnitBox
    .. autofunction:: createHalfStockButton
    .. autofunction:: createProgressBarWithLabel

    The :class:`EntryTableBuilder` Class
    ------------------------------------
    .. autoclass:: EntryTableBuilder
    .. automethod:: EntryTableBuilder.addNumberEntry
    .. automethod:: EntryTableBuilder.addWidget
    .. automethod:: EntryTableBuilder.buildTable

    Error Messages and Queries
    --------------------------
    .. autofunction:: reportError
    .. autofunction:: askUser

    Utility Functions
    -----------------
    .. autofunction:: isInWindow
    .. autofunction:: getToplevelWindow
    .. autofunction:: arrangeDefaulting

    Constants
    ---------
    .. autodata:: PANEL_BORDER_WIDTH
    .. autodata:: SPACING
    .. autodata:: NUMBER_ENTRY_WIDTH

    Test Support
    ------------
    The following attributes may be useful for testing code that calls
    :func:`reportError` or :func:`askUser`.

    .. autodata:: TESTING_SUPPRESS_REPORTS
    .. autodata:: TESTING_REPORT
    .. autodata:: TESTING_REPORT_ID
    .. autodata:: TESTING_DEFAULT_ANSWER
    .. autodata:: TESTING_QUESTION_ASKED
