:mod:`gui.io`
*************

.. automodule:: gui.io

.. autodata:: FILE_TYPES
.. autofunction:: load
.. autofunction:: save
.. autofunction:: read
.. autofunction:: write
.. autofunction:: chooseFile
.. autofunction:: stripPath

|

**Module Data**

.. data:: TESTING_USE_DEFAULT_FILE_NAME
          TESTING_DEFAULT_FILE_NAME

    If :data:`TESTING_USE_DEFAULT_FILE_NAME` is set to ``True``,
    :func:`chooseFile` returns :data:`TESTING_DEFAULT_FILE_NAME`
    rather than asking the user to choose a file. Intended for
    unit testing.

.. autodata:: READ_ERROR_MESSAGE
.. autodata:: WRITE_ERROR_MESSAGE
.. autodata:: PARSE_ERROR_MESSAGE

|

**Private Utiltiy Functions**

.. autofunction:: _createFileChooser
.. autofunction:: _runFileChooser
.. autofunction:: _addFileFilters

