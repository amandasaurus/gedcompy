import sys, re
from pprint import pprint

line_format = re.compile("^(?P<level>[0-9]+) ((?P<id>@[a-zA-Z0-9]+@) )?(?P<tag>[A-Z]+)( (?P<value>.*))?$")

class GedcomFile(object):
    """
    Represents a GEDCOM file.
    """
    def __init__(self):
        self.root_elements = []
        self.pointers = {}

    def __repr__(self):
        return "GedcomFile(\n"+",\n".join(repr(c) for c in self.root_elements)+")"

    def __getitem__(self, key):
        """
        Returns the element that has this pointer/id

        :param string key: Pointer for object (e.g. "@I33@")
        :returns: instance of Element (or subclass)
        """
        return self.pointers[key]

    def add_element(self, element):
        """
        
        """
        if element.id:
            self.pointers[element.id] = element
        if element.level == 0:
            self.root_elements.append(element)

    @property
    def individuals(self):
        """
        Returns all individuals in this file.
        :returns: List of Individual's
        """
        return (i for i in self.root_elements if isinstance(i, Individual))

class Element(object):
    """
    """

    def __init__(self, level, tag, value, id=None, parent_id=None, parent=None):
        self.level = level
        self.tag = tag
        self.value = value
        self.child_elements = []
        self.parent_element = parent
        self.id = id
        self.parent_id = parent_id

        if parent is not None:
            self.parent_element.child_elements.append(self)
            self.parent_id = self.parent_element.id

    def __repr__(self):
        return "{}(level={}, tag={}, id={}, parent_id={}, value={!r}, children={!r})".format(self.__class__.__name__, self.level, self.tag, self.id, self.parent_id, self.value, self.child_elements)

    def __getitem__(self, key):
        """
        Returns child element that has ``key`` as a tag,

        :param string key: tag name of child element you want
        :raises KeyError: If there are >1 child elements with this tag
        :raises IndexError: If there are no child elements with this tag
        :returns: Element
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
        Returns True iff there is at least one child element with this tag, False otherwise
        """
        return any(c.tag == key for c in self.child_elements)

    def get_by_id(self, other_id):
        """
        Returns an Element from the GEDCOM file with this id/pointer
        """
        return self.gedcom_file[other_id]

    def get_list(self, key):
        return [c for c in self.child_elements if c.tag == key]


tags_to_classes = {}

def class_for_tag(tag):
    """
    Internal class decorator to mark a python class as to be the handler for
    this tag
    """
    def classdecorator(klass):
        global tags_to_classes
        tags_to_classes[tag] = klass
        return klass
    return classdecorator

@class_for_tag("INDI")
class Individual(Element):

    @property
    def parents(self):
        """Returns list of parents of this person"""
        if 'FAMC' in self:
            family_as_child_id = self['FAMC'].value
            family = self.get_by_id(family_as_child_id)
            if not any(child.value == self.id for child in family.get_list("CHIL")):
                #raise Exception("Invalid family", family, self)
                pass
            parents = family.get_list('HUSB') + family.get_list("WIFE")
            parents = [p.as_individual() for p in parents]
            return parents
        else:
            return []
        
    @property
    def name(self):
        """
        This person's name

        :returns: (firstname, lastname)
        """
        name_tag = self['NAME']
        if name_tag.value == "":
            first = name_tag['GIVN'].value
            last = name_tag['SURN'].value
        else:
            first, last, dud = name_tag.value.split("/")
        
        return first, last

    @property
    def birth(self):
        """Class representing the birth of this person"""
        return self['BIRT']

    @property
    def death(self):
        """Class representing the death of this person"""
        return self['DEAT']

    @property
    def sex(self):
        return self['SEX'].value

    @property
    def gender(self):
        return self['SEX'].value

    @property
    def father(self):
        male_parents = [p for p in self.parents if p.is_male]
        if len(male_parents) == 0:
            return None
        elif len(male_parents) == 1:
            return male_parents[0]
        elif len(male_parents) > 1:
            raise NotImplementedError()

    @property
    def mother(self):
        female_parents = [p for p in self.parents if p.is_female]
        if len(female_parents) == 0:
            return None
        elif len(female_parents) == 1:
            return female_parents[0]
        elif len(female_parents) > 1:
            raise NotImplementedError()

    @property
    def is_female(self):
        return self.sex.lower() == 'f'

    @property
    def is_male(self):
        return self.sex.lower() == 'm'

@class_for_tag("FAM")
class Family(Element): pass

class Spouse(Element):
    # Generic tag class
    def as_individual(self):
        return self.gedcom_file[self.value]

@class_for_tag("HUSB")
class Husband(Spouse): pass

@class_for_tag("WIFE")
class Wife(Spouse): pass

@class_for_tag("WIFE")
class Wife(Spouse): pass

class Event(Element):
    @property
    def date(self):
        return self['DATE'].value

    @property
    def place(self):
        return self['PLAC'].value

@class_for_tag("BIRT")
class Birth(Event): pass

@class_for_tag("DEAT")
class Death(Event): pass


def line_to_element(**line_dict):
    if line_dict['tag'] in tags_to_classes:
        return tags_to_classes[line_dict['tag']](**line_dict)
    else:
        return Element(**line_dict)

def parse_filename(filename):
    """
    Parse filename and return GedcomFile

    :param string filename: Filename to parse
    :returns: GedcomFile instance
    """
    with open(filename, 'r') as fp:
        return parse(fp)

def parse(file_fp):
    """
    Parse file and return GedcomFile

    :param filehandle file_fp: open file handle for input
    :returns: GedcomFile instance
    """
    current_level = 0
    level_to_obj = {}
    gedcom_file = GedcomFile()

    for linenum, line in enumerate(file_fp.readlines()):
        line = line.strip()
        match = line_format.match(line)
        if not match:
            raise NotImplementedError()

        level = int(match.groupdict()['level'])
        
        if level == 0:
            parent = None
        else:
            level_to_obj = dict((l, obj) for l, obj in level_to_obj.items() if l < level)
            parent = level_to_obj[level-1]


        element = line_to_element(level=level, parent=parent, tag=match.groupdict()['tag'], value=match.groupdict()['value'], id=match.groupdict()['id'])
        level_to_obj[level] = element
        element.gedcom_file = gedcom_file
        gedcom_file.add_element(element)

    return gedcom_file

