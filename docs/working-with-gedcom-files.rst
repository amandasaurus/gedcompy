Example Usage
-------------

    >>> import gedcom
    >>> gedcomfile = gedcom.parse("myfamilytree.ged")
    >>> for person in gedcomfile.individuals:
    ...    firstname, lastname = person.name
    ...    print "{0} {1} is in the file".format(firstname, lastname)
