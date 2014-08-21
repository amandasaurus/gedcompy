"""
Library for reading and writing GEDCOM files.

https://en.wikipedia.org/wiki/GEDCOM
"""
import re
import numbers
import os.path
import six

__version__ = "0.1.0"

line_format = re.compile("^(?P<level>[0-9]+) ((?P<id>@[a-zA-Z0-9]+@) )?(?P<tag>[A-Z]+)( (?P<value>.*))?$")


class GedcomFile(object):

    """ Represents a GEDCOM file.  """

    def __init__(self):
        """Instanciate a GEDCOM object."""
        self.root_elements = []
        self.pointers = {}
        self.next_free_id = 1

    def __repr__(self):
        """String represenation of GEDCOM. For internal debugging purposes only."""
        return "GedcomFile(\n" + ",\n".join(repr(c) for c in self.root_elements) + ")"

    def __getitem__(self, key):
        """
        Return the element that has this pointer/id in this file.

        :param string key: Pointer for object (e.g. "@I33@")
        :returns: Element with this id
        :rtype: :py:class:`Element`
        :raises KeyError: If key is not in this file
        """
        return self.pointers[key]


    def add_element(self, element):
        """
        Add an Element to this file.

        If element.level is unset, it'll presume it's a top level element, and set the level and id appropriately.

        :param :py:class:`Element` element: Element to add
        """
        if element.level is None:
            # Need to figure out an element
            if not ( isinstance(element, Individual) or isinstance(element, Family)):
                raise TypeError()
            element.level = 0
            element.set_levels_downward()

            # create pointer
            if isinstance(element, Individual):
                prefix = 'I'
            elif isinstance(element, Family):
                prefix = 'F'
            else:
                raise NotImplementedError()

            for step in range(1, 1000000):
                potential_id = "@{prefix}{num}@".format(prefix=prefix, num=self.next_free_id)
                if potential_id in self.pointers:
                    # this number is taken, increase
                    self.next_free_id += 1
                else:
                    # Found a free id
                    element.id = potential_id
                    self.next_free_id += 1
                    break
            else:
                # Tried 1,000,000 times and didn't have a free id? weird!
                # prevents an infinite loop
                raise Exception("Ran out of ids?")


        element.gedcom_file = self
        if element.id:
            self.pointers[element.id] = element
        if element.level == 0:
            self.root_elements.append(element)


    @property
    def individuals(self):
        """
        Iterator of all Individual's in this file.

        :returns: iterator of Individual's
        :rtype: iterator
        """
        return (i for i in self.root_elements if isinstance(i, Individual))

    @property
    def families(self):
        """
        Iterator of all Family's in this file.

        :returns: iterator of Families's
        :rtype: iterator
        """
        return (i for i in self.root_elements if isinstance(i, Family))

    def gedcom_lines(self):
        """
        Iterator that returns the lines in this file.

        :returns: iterator over lines
        :rtype: iterator
        """
        self.ensure_header_trailer()
        for el in self.root_elements:
            for line in el.gedcom_lines():
                yield line

    def gedcom_lines_as_string(self):
        """
        Return this file as a string.

        :returns: Full encoded text of this file
        :rtype: string
        """
        return "\n".join(self.gedcom_lines())


    def ensure_header_trailer(self):
        """
        If GEDCOM file does not have a header (HEAD) or trailing element (TRLR), it will be added. If those exist they won't be added.

        Call this method to ensure the file has these required elements.
        """
        if len(self.root_elements) == 0 or self.root_elements[0].tag != 'HEAD':
            # add header
            head_element = self.element('HEAD', level=0, value='')
            source = self.element("SOUR")
            source.add_child_element(self.element("NAME", value="gedcompy"))
            source.add_child_element(self.element("VERS", value=__version__))
            head_element.add_child_element(source)
            head_element.add_child_element(self.element("CHAR", value="UNICODE"))
            head_element.set_levels_downward()
            self.root_elements.insert(0, head_element)
        if len(self.root_elements) == 0 or self.root_elements[-1].tag != 'TRLR':
            # add trailer
            self.root_elements.append(self.element('TRLR', level=0, value=''))

    def element(self, tag, **kwargs):
        """
        Return a new Element that is in this file.
        :param str tag: tag name for this object
        :param **kwargs: Passed to Element constructor
        :rtype: Element or subclass based on `tag`
        """
        klass = class_for_tag(tag)
        return klass(gedcom_file=self, tag=tag, **kwargs)

    def individual(self, **kwargs):
        return self.element("INDI", **kwargs)

    def family(self, **kwargs):
        return self.element("FAM", **kwargs)



class Element(object):

    """
    Generic represetation for a GEDCOM element.
    
    Can be used as is, or subclassed for specific functionality.
    """

    def __init__(self, level=None, tag=None, value=None, id=None, parent_id=None, parent=None, gedcom_file=None):
        """
        Create an element.

        :param int level: The level of this element (0, 1, 2, ...)
        :param str tag: GEDCOM tag (e.g. 'FAM', 'INDI', 'DATE', etc.)
        :param str value: *optional* value for this tag
        :param string parent_id: ID/Pointer for the parent element for this element.
        :param Element parent: The actual parent element of this object.
        :param GedcomFile gedcom_file: File this element is in (used for lookups)
        """
        self.level = level
        if tag is not None:
            if hasattr(self, 'default_tag'):
                if tag != self.default_tag:
                    raise ValueError("Tag {} differs from default {}".format(tag, self.default_tag))
            self.tag = tag
        else:
            self.tag = self.default_tag
        self.value = value
        self.child_elements = []
        self.parent_element = parent
        self.id = id
        self.parent_id = parent_id
        self.gedcom_file = gedcom_file

        if parent is not None:
            self.parent_element.add_child_element(self)

    def __repr__(self):
        """Interal string represation of this object, for debugging purposes."""
        return "{classname}({level}, {tag!r}{id}{value}{children})".format(
            classname=self.__class__.__name__, level=self.level, tag=self.tag, id=(", "+repr(self.id) if self.id else ""),
            value=(", "+repr(self.value) if self.value else ""), children=(", "+repr(self.child_elements) if len(self.child_elements) > 0 else ""))

    def __getitem__(self, key):
        """
        Get the child element that has ``key`` as a tag.

        :param string key: tag name of child element you want
        :raises KeyError: If there are >1 child elements with this tag
        :raises IndexError: If there are no child elements with this tag
        :returns: Element
        :rtype: Element (or subclass)
        """
        children = [c for c in self.child_elements if c.tag == key]
        if len(children) == 0:
            raise IndexError(key)
        elif len(children) == 1:
            return children[0]
        elif len(children) > 1:
            raise KeyError(key)

    def __contains__(self, key):
        """
        Return True iff there is at least one child element with this tag, False otherwise.

        :param str key: Tag to look for.
        """
        return any(c.tag == key for c in self.child_elements)

    def add_child_element(self, child_element):
        """
        Add `child_element` as a child of this.

        It sets the :py:attr:`parent` and :py:attr:`parent_id` of `child_element` to this
        element, but does not set the :py:meth:`level`. See
        :py:meth:`set_levels_downward` to correct that.

        :param Element child_element: The Element you want to add as a child.
        """
        child_element.parent = self
        child_element.parent_id = self.id
        child_element.gedcom_file = self.gedcom_file
        self.child_elements.append(child_element)

    def get_by_id(self, other_id):
        """
        Return an Element from the GEDCOM file with this id/pointer.

        :param str other_id: ID/Pointer of element to search for
        :returns: Element with ID
        :rtype: Element
        :raises KeyError: If this id/pointer doesn't exist in the file
        """
        return self.gedcom_file[other_id]

    def get_list(self, tag):
        """
        Return a list of all child elements that have this tag.

        :param str tag: Tag to search for (e.g. 'DATE')
        :returns: list of any child nodes that have this tag
        :rtype: list
        """
        return [c for c in self.child_elements if c.tag == tag]

    def set_levels_downward(self):
        """Set all :py:attr:`level` attributes for all child elements recursively, based on the :py:attr:`level` for this object."""
        if not isinstance(self.level, numbers.Integral):
            raise TypeError(self.level)
        for c in self.child_elements:
            c.level = self.level + 1
            c.gedcom_file = self.gedcom_file
            c.set_levels_downward()

    def gedcom_lines(self):
        """
        Iterator over the encoded lines for this element.

        :rtype: iterator over string
        """
        line_format = re.compile("^(?P<level>[0-9]+) ((?P<id>@[a-zA-Z0-9]+@) )?(?P<tag>[A-Z]+)( (?P<value>.*))?$")
        line = "{level}{id} {tag}{value}".format(level=self.level, id=(" "+self.id if self.id else ""), tag=self.tag, value=(" "+self.value if self.value else ""))
        yield line
        for child in self.child_elements:
            for line in child.gedcom_lines():
                yield line
            


tags_to_classes = {}


def register_tag(tag):
    """ Internal class decorator to mark a python class as to be the handler for this tag.  """
    def classdecorator(klass):
        global tags_to_classes
        tags_to_classes[tag] = klass
        klass.default_tag = tag
        return klass
    return classdecorator


@register_tag("INDI")
class Individual(Element):

    """Represents and INDI (Individual) element."""

    @property
    def parents(self):
        """
        Return list of parents of this person.

        NB: There may be 0, 1, 2, 3, ... elements in this list.
    
        :returns: List of Individual's
        """
        if 'FAMC' in self:
            family_as_child_id = self['FAMC'].value
            family = self.get_by_id(family_as_child_id)
            if not any(child.value == self.id for child in family.get_list("CHIL")):
                # raise Exception("Invalid family", family, self)
                pass
            parents = family.get_list('HUSB') + family.get_list("WIFE")
            parents = [p.as_individual() for p in parents]
            return parents
        else:
            return []

    @property
    def name(self):
        """
        Return this person's name.

        :returns: (firstname, lastname)
        """
        name_tag = self['NAME']
        if name_tag.value == "":
            first = name_tag['GIVN'].value
            last = name_tag['SURN'].value
        else:
            first, last, dud = name_tag.value.split("/")
            first = first.strip()
            last = last.strip()

        return first, last

    @property
    def birth(self):
        """Class representing the birth of this person."""
        return self['BIRT']

    @property
    def death(self):
        """Class representing the death of this person."""
        return self['DEAT']

    @property
    def sex(self):
        """
        Return the sex of this person, as the string 'M' or 'F'.

        NB: This should probably support more sexes/genders.

        :rtype: str
        """
        return self['SEX'].value

    @property
    def gender(self):
        """
        Return the sex of this person, as the string 'M' or 'F'.

        NB: This should probably support more sexes/genders.

        :rtype: str
        """
        return self['SEX'].value

    @property
    def father(self):
        """
        Calculate and return the individual represenating the father of this person.
        
        Returns `None` if none found.

        :return: the father, or `None` if not in file.
        :raises NotImplementedError: If it cannot figure out who's the father.
        :rtype: :py:class:`Individual`
        """
        male_parents = [p for p in self.parents if p.is_male]
        if len(male_parents) == 0:
            return None
        elif len(male_parents) == 1:
            return male_parents[0]
        elif len(male_parents) > 1:
            raise NotImplementedError()

    @property
    def mother(self):
        """
        Calculate and return the individual represenating the mother of this person.
        
        Returns `None` if none found.

        :return: the mother, or `None` if not in file.
        :raises NotImplementedError: If it cannot figure out who's the mother.
        :rtype: :py:class:`Individual`
        """
        female_parents = [p for p in self.parents if p.is_female]
        if len(female_parents) == 0:
            return None
        elif len(female_parents) == 1:
            return female_parents[0]
        elif len(female_parents) > 1:
            raise NotImplementedError()

    @property
    def is_female(self):
        """ Return True iff this person is recorded as female. """
        return self.sex.lower() == 'f'

    @property
    def is_male(self):
        """ Return True iff this person is recorded as male. """
        return self.sex.lower() == 'm'

    def set_sex(self, sex):
        """
        Set the sex for this person.

        :param str sex: 'M' or 'F' for male or female resp.
        :raises TypeError: if `sex` is invalid
        """
        sex = sex.upper()
        if sex not in ['M', 'F']:
            raise TypeError("Currently only support M or F")
        try:
            sex_node = self['SEX']
            sex_node.value = sex
        except IndexError:
            self.add_child_element(self.gedcom_file.element("SEX", value=sex))



@register_tag("FAM")
class Family(Element):

    """Represents a family 'FAM' tag."""

    pass


class Spouse(Element):
    
    """Generic base class for HUSB/WIFE."""

    def as_individual(self):
        """
        Return the :py:class:`Individual` for this object.

        :returns: the individual
        :rtype: :py:class:`Individual`
        :raises KeyError: if id/pointer not found in the file.
        """
        return self.gedcom_file[self.value]


@register_tag("HUSB")
class Husband(Spouse):

    """Represents pointer to a husband in a family."""

    pass


@register_tag("WIFE")
class Wife(Spouse):

    """Represents pointer to a husband in a family."""

    pass


class Event(Element):

    """Generic base class for events, like :py:class:`Birth` (BIRT) etc."""

    @property
    def date(self):
        """
        Get the Date of this event, from the 'DATE' tagged child element.

        :returns: date value
        :rtype: string
        :raises KeyError: if there is no DATE sub-element
        """
        return self['DATE'].value

    @property
    def place(self):
        """
        Get the place of this event, from the 'PLAC' tagged child element.

        :returns: date value
        :rtype: string
        :raises KeyError: if there is no PLAC sub-element
        """
        return self['PLAC'].value


@register_tag("BIRT")
class Birth(Event):

    """Represents a birth (BIRT)."""

    pass


@register_tag("DEAT")
class Death(Event):

    """Represents a death (DEAT)."""

    pass


@register_tag("MARR")
class Marriage(Event):

    """Represents a marriage (MARR)."""

    pass


def class_for_tag(tag):
    """
    Return the class object for this `tag`
    :param str tag: tag (e.g. INDI)
    :rtype: class (Element or something that's a subclass)
    """
    global tags_to_classes
    return tags_to_classes.get(tag, Element)


def line_to_element(**line_dict):
    """
    Return an instance of :py:class:`Element` (or subclass) based on these parsed out values from :py:const:`line_regex`.

    :rtype: Element or subclass
    """
    return class_for_tag(line_dict['tag'])(**line_dict)


def parse_filename(filename):
    """
    Parse filename and return GedcomFile.

    :param string filename: Filename to parse
    :returns: GedcomFile instance
    """
    with open(filename, 'r') as fp:
        return __parse(fp.readlines())


def parse_string(string):
    """
    Parse filename and return GedcomFile.

    :param str string: Filename to parse
    :returns: GedcomFile instance
    """
    return __parse(string.split("\n"))


def parse_fp(file_fp):
    """
    Parse file and return GedcomFile.

    :param filehandle file_fp: open file handle for input
    :returns: GedcomFile instance
    """
    return __parse(file_fp.readlines())

def parse(obj):
    """
    Parse and return this object, if it's a file
    """
    if isinstance(obj, six.string_types):
        # Sanity check, presumes anything > 1KB could not be a filename
        if len(obj) <= 1024 and os.path.exists(obj):
            return parse_filename(obj)
        else:
            return parse_string(obj)
    else:
        return parse_fp(obj)


def __parse(lines_iter):
    current_level = 0
    level_to_obj = {}
    gedcom_file = GedcomFile()

    for linenum, line in enumerate(lines_iter):
        line = line.strip()
        if line == '':
            continue
        match = line_format.match(line)
        if not match:
            raise NotImplementedError(line)

        level = int(match.groupdict()['level'])

        if level == 0:
            parent = None
        else:
            level_to_obj = dict((l, obj) for l, obj in level_to_obj.items() if l < level)
            parent = level_to_obj[level - 1]

        element = line_to_element(level=level, parent=parent, tag=match.groupdict()['tag'], value=match.groupdict()['value'], id=match.groupdict()['id'])
        level_to_obj[level] = element
        element.gedcom_file = gedcom_file
        gedcom_file.add_element(element)

    return gedcom_file
