gedcompy
========

.. image:: https://travis-ci.org/rory/gedcompy.svg?branch=master
    :target: https://travis-ci.org/rory/gedcompy

.. image:: https://coveralls.io/repos/rory/gedcompy/badge.png?branch=master
  :target: https://coveralls.io/r/rory/gedcompy?branch=master


Python library to parse and work with `GEDCOM <https://en.wikipedia.org/wiki/GEDCOM>`_ (genealogy/family tree) files.

It's goal is to support GEDCOM v5.5 (`specification here <http://homepages.rootsweb.ancestry.com/~pmcbride/gedcom/55gctoc.htm>`_).

This is released under the GNU General Public Licence version 3 (or at your option, a later version). See the file `LICENCE` for more.

Example Usage
-------------
```python
    >>> import gedcom
    >>> gedcomfile = gedcom.parse("myfamilytree.ged")
    >>> for person in gedcomfile.individuals:
    ...    firstname, lastname = person.name
    ...    print "{0} {1} is in the file".format(firstname, lastname)
```

Available Usage
--------------
### options
```python
>>> for person in gedcomfile.individuals:
...     print person.birth.date
...     print person.birth.place
...     print person.death.date
...     print person.death.place
...     print person.sex     
```
### dates
Dates are user input and can vary wildly in formatting. There are also approximate dates that cannot be formatted. 
These approximate dates can be stripped out using `re` or just `str.replace()`

Using pythons <a href='https://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior'>`datetime`</a> library (specifically `strftime` and `strptime`. the dates available can be formatted by looping through various date formats using try/except.

```python
>>> dateFormats = ['%m/%d/%Y', '%m-%d-%Y', '%d-%m-%Y', '%d %b %Y'] #just a few examples
>>> for person in filename.individuals:
...     for i in dateFormat:
...         try:
...             print datetime.strptime(person.birth.date, i)
...         except ValueError: # ValueError will be thrown when the date given does not match the formatting provided from the dateFormat list
...             pass
```
To discover more dates add a counter and increment as it passes through the dateFormat list. If the counter is higher than the length of the list -1 raise an exception printing the date that broke the program.

> TODO: Family Relations

Contributing
------------

Run all unitttests with `tox`.

