Localizing the Application
==========================

The following steps are required to localize the application:

#) Run ``find nose -name "*.py" | xgettext -f -`` in the application's main
   directory. A file named ``messages.po`` should be created.

#) Run :samp:`msginit -l {LL} -i messages.po`, where :samp:`{LL}` is the target
   locale (e.g. ``de`` or ``de_DE`` for German). Answer the questions. A file
   named :samp:`{LL}.po` should be created.

#) Translate the messages in :samp:`{LL}.po`.

#) Run :samp:`msgfmt -cv {LL}.po -o nose.mo`. A file named ``nose.mo`` should
   be created.

#) Move ``nose.mo`` to :samp:`resources/messages/{LL}/LC_MESSAGES/`.

#) Rejoice.


The contents of some translatable messages require special handling:

* Some messages contain `formatting specifiers <http://docs.python.org/
  library/stdtypes.html#string-formatting-operations>`_ such as ``%s`` or
  ``%(totalTimeLeft)s``. These will be replaced by appropriate parameters
  when the application uses the string. Their respective functions should be
  discernible from context. Note that keywords such as the ``totalTimeLeft``
  above must not be translated. ``msgfmt`` will check that these specifiers
  aren't broken during translation, and will terminate with an error message
  if they are.

* Some messages contain tags that may look like HTML (``<i>`` and ``<sup>``).
  These are actually `Pango Markup Language <http://www.pygtk.org/docs/pygtk/
  pango-markup-language.html>`_ tags. Breaking them will trigger a
  :class:`PangoWarning` when the application uses them. The message in question
  will not be shown at all, or will be replaced with another message used
  nearby. In messages that don't already have such tags, added tags almost
  certainly won't be interpreted.

* Some messages define keyboard accelerators (e.g. ``<Shift><Ctrl>C``). These
  can safely be changed to whatever accelerator makes sense in the target
  language. Breaking them will trigger a :class:`GtkWarning` when the
  application uses them. The message containing the text of the menu item they
  are used on should immediately precede the message defining the accelerator.

* Some messages contain underscores. These define the next character as a
  mnemonic. These mnemonics can safely be shifted to other letters. Mnemonics
  defined significant distances from each other may be used in the same window,
  however, so special care must be taken to ensure that no character is used
  as a mnemonic more than once in any single window. If a mnemonic is used
  on several widgets in the same window, using it will select each of the
  widgets in sequence.

* One message, ``{{MIN_CAPTION_LINES}}``, is an abuse of ``gettext`` that
  allows the value of :data:`gui.calibration.charts.MIN_CAPTION_LINES` to be
  set as part of the localization procedure. The application ties to parse the
  localized message as an integer and uses the result to set the constant if
  successful.

