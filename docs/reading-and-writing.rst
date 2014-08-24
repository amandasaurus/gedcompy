Reading GEDCOM files
--------------------

The function :py:func:`gedcom.parse` reads a file, string, or file-like object and returns a :py:class:`gedcom.GedcomFile`.

.. autofunction:: gedcom.parse

Writing GEDCOM files
--------------------

:py:func:`gedcom.GedcomFile.save` saves a :py:class:`gedcom.GedcomFile` to a specified filename, or file-like object.

.. automethod:: gedcom.GedcomFile.save
