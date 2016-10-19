gedcompy
========

<img src='https://travis-ci.org/rory/gedcompy.svg?branch=master' />
<img src='https://coveralls.io/repos/rory/gedcompy/badge.png?branch=master' />


Python library to parse and work with <a href='https://en.wikipedia.org/wiki/GEDCOM'>`GEDCOM`</a> (genealogy/family tree) files.

It's goal is to support GEDCOM v5.5 (<a href='http://homepages.rootsweb.ancestry.com/~pmcbride/gedcom/55gctoc.htm'>`Specification Here`</a>).

This is released under the GNU General Public Licence version 3 (or at your option, a later version). See the file `LICENCE` for more.

## gedcompy Usage:
gedcompy parses out the records of each person and stores them as nested objects, accesible through dot notation.

Example Usage
-------------
```python
    >>> import gedcom
    >>> gedcomfile = gedcom.parse("myfamilytree.ged")
    >>> for person in gedcomfile.individuals:
    ...    firstname, lastname = person.name
    ...    print "{0} {1} is in the file".format(firstname, lastname)
```

The file as a whole is a generator object.

```python
>>> import gedcom
>>> gedfile = gedcom.parse("myfamilytree.ged")
>>> print gedfile
# GedcomFile(Element(0, 'HEAD', [Element(1, 'CHAR', 'UTF-8'), Element(1, 'SOUR', 'Ancestry.com Family Trees', [Element(2, 'VERS', '(2010.3)'), Element(2, 'NAME', 'Ancestry.com Family Trees'), Element(2, 'CORP', 'Ancestry.com')]), Element(1, 'GEDC', [Element(2, 'VERS', '5.5'), Element(2, 'FORM', 'LINEAGE-LINKED')])]),
# Individual(0, 'INDI', '@P1@', [Birth(1, 'BIRT', [Element(2, 'DATE', '03 dec 1970')]), Element(1, 'SEX', 'M'), Element(1, 'NAME', 'John /Smith/'), Element(1, 'FAMC', '@F1@')])
# Individual(0, 'INDI', '@P2@', [Element(1, 'NAME', 'Jane /Doe/'), Element(1, 'SEX', 'M'), Birth(1, 'BIRT', [Element(2, 'DATE', '06 nov 1946'), Element(2, 'PLAC', 'Brooklyn, New York City, New York, USA')]), Element(1, 'FAMS', '@F1@')])
```

### Individuals
Cannot access individuals as a whole:

```python
>>> print gedfile.individuals
# <generator object <genexpr> at 0x103ef25a0>
>>> print gedfile.individual # Probably Don't.
# Don't do this. It prints all individual records in the file.
```

To access individual records:

```python
>>> for person in gedfile.individuals:
...     print person
# Individual(0, 'INDI', '@P1@', [Birth(1, 'BIRT', [Element(2, 'DATE', '03 dec 1970')]), Element(1, 'SEX', 'M'), Element(1, 'NAME', 'John /Smith/'), Element(1, 'FAMC', '@F1@')])
# Individual(0, 'INDI', '@P2@', [Element(1, 'NAME', 'Jane /Doe/'), Element(1, 'SEX', 'M'), Birth(1, 'BIRT', [Element(2, 'DATE', '06 nov 1946'), Element(2, 'PLAC', 'Brooklyn, New York City, New York, USA')]), Element(1, 'FAMS', '@F1@')])
```
To access individual records of a specific type use dot notation:

```python
>>> for person in gedfile.individuals:
...     print person.birth
# Birth(1, 'BIRT', [Element(2, 'DATE', '03 dec 1970')])
# Birth(1, 'BIRT', [Element(2, 'DATE', '06 nov 1946'), Element(2, 'PLAC', 'Brooklyn, New York City, New York, USA')])
```

To specify individual record types:

```python
>>> for person in gedfile.individuals:
...     print person.birth.date
# 03 dec 1970
# 06 nov 1946
>>> for person in gedfile.individuals:
...     print person.birth.place
# AttributeError: 'NoneType' object has no attribute 'value'
# this does not print: Brooklyn, New York City, New York, USA
```
The AttributeError is thrown when a record of that type does not exist, and by default will NOT pass onto the next record.


##### current available use cases
```
person.birth              # class - birth
person.birth.place        # string
person.birth.date         # string
person.death              # class - death
person.death.place        # string
person.death.date         # string
person.name               # tuple - firstname, lastname
person.father             # class - father
person.mother             # class - mother
person.parents            # list - contaning father and mother class
person.aka                # list - 'also known as' name
person.gender             # string - 'M' or 'F'
person.sex                # string - ''     ''
person.id                 # string - @P12@
person.is_female          # boolean
person.is_male            # boolean
person.note               # string
person.title              # string
person.default_tag        # string tagname : 'INDI', 'FAM', etc
person.tag                # string tagname : 'INDI', 'FAM', etc

```

#### Advanced usage

Get the name of a person and parents of that person:

```python
>>> for person in gedfile.individuals:
...     try:
...         print person.name, person.parents[0].name, person.parents[1].name
...     except IndexError:
...         print "no parent name record for this person"
# OR
>>> for person in gedfile.individual:
...     try:
...         print person.name, person.father.name, person.mother.name
...     except AttributeError:
...        print "no parent name record for this person"
# either one will print:
# ('John', 'Doe') ('Jack', 'Doe') ('Jane', 'Doe')
# ('Jenny', 'Doe') ('Jack', 'Doe') ('Jane', 'Doe')
```

### Families

Family records are accessed the same way as individuals

```python
>>> print gedfile.families
# <generator object <genexpr> at 0x10523c7d0>
>>> print gedfile.family # Probably don't.
# Don't do this. Prints all family records in the family
```

```python
>>> for family in gedfile.families:
...     print family
# Family(0, 'FAM', '@F1@', [Husband(1, 'HUSB', '@P5@'), Wife(1, 'WIFE', '@P1@'), Element(1, 'CHIL', '@P2@', [Element(2, '_FREL', 'Natural'), Element(2, '_MREL', 'Natural')])])

>>> for family in gedfile.families:
...     print family.partners
# [Husband(1, 'HUSB', '@P5@'), Wife(1, 'WIFE', '@P1@')]
```

Use cases for partners:

```python
>>> for family in gedfile.families:
...     print family.partners[0]
...     print family.partners[1]
# Husband(1, 'HUSB', '@P5@')
# Wife(1, 'WIFE', '@P1@')

>>> for family in gedfile.families:
...     print family.partners[0].tag
# HUSB

>>> for family in gedfile.families:
...     print family.partners[0].value
# @P5@

>>> for family in gedfile.families:
...     print family.husband
...     print family.wife
# Husband(1, 'HUSB', '@P5@')
# Wife(1, 'WIFE', '@P1@')
```

Use cases for children

##### current available use cases

```
family.id                       # string '@F49@'
family.tag                      # string 'FAM'
family.partners                 # list 
family.wife                     # class - wife
family.husband                  # class - husband
family.children                 # list
family.children.father_relation # String 'Natural'
family.children.mother_relation # string 'Natural'
```

### Residence
Residence records

```python
>>> for person in gedfile.individuals
...			print person.residence
# Residence(1, 'RESI', 'Marital Status: SingleRelation to Head of House: Son', [Element(2, 'DATE', '1910'), Element(2, 'PLAC', 'Lowell Ward 6, Middlesex, Massachusetts, USA'), Source(2, 'SOUR', '@S1002094821@', [Element(3, 'PAGE', 'Year: 1910; Census Place: Lowell Ward 6, Middlesex, Massachusetts; Roll: T624_600; Page: 33A; Enumeration District: 0864; FHL microfilm: 1374613'), Element(3, '_APID', '1,7884::108099427')])])
>>> for person in gedfile.individuals
...			print person.residence.date
...			print person.residence.source
# 1910
# @S100243564@
```

##### current available use cases
```
residence.date
residence.id
residence.note
residence.parent_id
residence.place
residence.source
residence.value
```

### Error Handling
By default, if a record doesn't exist an error will be raised and will not continue onto the rest of the records. This is on purpose, but can by bypassed by using try/except cases. The most common errors that are raised are IndexError and AttributeError

```python
>>> for person in gedfile.individuals:
...     try:
...         print person.birth.place
...     except AttributeError:
...         print "There is no birth place record for this person"
# There is no birth place record for this person
# Brooklyn, New York City, New York, USA
```
```python
>>> for family in gedfile.families:
...     try:
...         print family.marriage
...     except IndexError as e:
...         print "no record: ", e
# Marriage(1, 'MARR', [Element(2, 'DATE', '08 Aug 1854')])
# no record: IndexError: list index out of range
# Marriage(1, 'MARR', [Element(2, 'DATE', '1954')])
```

### Dates
Dates are user input and can vary wildly in formatting. There are also approximate dates that cannot be formatted. 
These approximate dates can be stripped out using `re` or just `str.replace()`

Using pythons <a href='https://docs.python.org/2/library/datetime.html'>`datetime`</a> library (specifically <a href='https://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior'>`strftime`</a> & <a href='https://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior'>`strptime`</a>. the dates available can be formatted by looping through various date formats using try/except.

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


Contributing
------------

Run all unitttests with `tox`.

