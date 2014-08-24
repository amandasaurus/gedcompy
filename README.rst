gedcompy
========

.. image:: https://travis-ci.org/rory/gedcompy.svg?branch=master
    :target: https://travis-ci.org/rory/gedcompy

.. image:: https://coveralls.io/repos/rory/gedcompy/badge.png?branch=master
  :target: https://coveralls.io/r/rory/gedcompy?branch=master


Python library to parse and work with `GEDCOM <https://en.wikipedia.org/wiki/GEDCOM>`_ (geneology/family tree) files.

It's goal is to support GEDCOM v5.5 (`specification here <http://homepages.rootsweb.ancestry.com/~pmcbride/gedcom/55gctoc.htm>`_).

This is released under the GNU General Public Licence version 3 (or at your option, a later version). See the file `LICENCE` for more.

Example Usage
-------------

    >>> import gedcom
    >>> gedcomfile = gedcom.parse("myfamilytree.ged")
    >>> for person in gedcomfile.individuals:
    ...    firstname, lastname = individual.name
    ...    print "{0} {1} is in the file".format(firstname, lastname)


Contributing
------------

Run all unitttests with `tox`.

