# encoding: utf-8
import unittest
import gedcom
import six
import tempfile
from os import remove
import codecs

# Sample GEDCOM file from Wikipedia
GEDCOM_FILE = """0 HEAD
1 SOUR Reunion
2 VERS V8.0
2 CORP Leister Productions
1 DEST Reunion
1 DATE 11 FEB 2006
1 FILE test
1 GEDC
2 VERS 5.5
1 CHAR MACINTOSH
0 @I1@ INDI
1 NAME Robert /Cox/
1 NAME Bob /Cox/
2 TYPE aka
1 NAME
2 GIVN Rob
2 SURN Cox
2 TYPE aka
1 SEX M
1 FAMS @F1@
1 CHAN
2 DATE 11 FEB 2006
0 @I2@ INDI
1 NAME Joann /Para/
1 SEX F
1 FAMS @F1@
1 CHAN
2 DATE 11 FEB 2006
0 @I3@ INDI
1 NAME Bobby Jo /Cox/
1 SEX M
1 FAMC @F1@
1 CHAN
2 DATE 11 FEB 2006
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
1 MARR
1 CHIL @I3@
0 TRLR
"""

def v(string):
    return string.format(version=gedcom.__version__)


class GedComTestCase(unittest.TestCase):

    def testCanParse(self):
        parsed = gedcom.parse_string(GEDCOM_FILE)
        self.assertTrue(isinstance(parsed, gedcom.GedcomFile))

        people = list(parsed.individuals)
        self.assertTrue(len(people), 3)

        bob = people[0]
        self.assertEquals(bob.name, ("Robert", "Cox"))
        self.assertEquals(bob.aka, [("Bob", "Cox"), ('Rob', 'Cox')])
        self.assertEquals(bob.sex, 'M')
        self.assertEquals(bob.gender, 'M')
        self.assertTrue(bob.is_male)
        self.assertFalse(bob.is_female)
        self.assertEquals(bob.parents, [])
        self.assertEquals(bob.father, None)
        self.assertEquals(bob.mother, None)

        joann = people[1]
        self.assertEquals(joann.name, ("Joann", "Para"))
        self.assertEquals(joann.sex, 'F')
        self.assertEquals(joann.gender, 'F')
        self.assertFalse(joann.is_male)
        self.assertTrue(joann.is_female)
        self.assertEquals(joann.parents, [])

        bobby_jo = people[2]
        self.assertEquals(bobby_jo.name, ("Bobby Jo", "Cox"))
        self.assertEquals(bobby_jo.sex, 'M')
        self.assertEquals(bobby_jo.gender, 'M')
        self.assertTrue(bobby_jo.is_male)
        self.assertFalse(bobby_jo.is_female)
        self.assertEquals(bobby_jo.parents, [bob, joann])
        self.assertEquals(bobby_jo.father, bob)
        self.assertEquals(bobby_jo.mother, joann)

        families = list(parsed.families)
        self.assertEquals(len(families), 1)
        family = families[0]
        self.assertEquals(family.__class__, gedcom.Family)
        self.assertEquals([p.as_individual() for p in family.partners], [bob, joann])

    def testCreateEmpty(self):
        gedcomfile = gedcom.GedcomFile()
        self.assertEqual(gedcomfile.gedcom_lines_as_string(), v('0 HEAD\n1 SOUR\n2 NAME gedcompy\n2 VERS {version}\n1 CHAR UNICODE\n1 GEDC\n2 VERS 5.5\n2 FORM LINEAGE-LINKED\n0 TRLR'))


    def testCanCreate(self):
        gedcomfile = gedcom.GedcomFile()
        individual = gedcomfile.individual()
        individual.set_sex("M")
        self.assertEquals(individual.level, 0)

        self.assertEquals(list(gedcomfile.individuals)[0], individual)

        self.assertEquals(individual.tag, 'INDI')
        self.assertEquals(individual.level, 0)
        self.assertEquals(individual.note, None)

        family = gedcomfile.family()

        self.assertEquals(family.tag, 'FAM')
        self.assertEquals(family.level, 0)

        self.assertEqual(gedcomfile.gedcom_lines_as_string(), v('0 HEAD\n1 SOUR\n2 NAME gedcompy\n2 VERS {version}\n1 CHAR UNICODE\n1 GEDC\n2 VERS 5.5\n2 FORM LINEAGE-LINKED\n0 @I1@ INDI\n1 SEX M\n0 @F2@ FAM\n0 TRLR'))
        self.assertEqual(repr(gedcomfile), v("GedcomFile(\nElement(0, 'HEAD', [Element(1, 'SOUR', [Element(2, 'NAME', 'gedcompy'), Element(2, 'VERS', '{version}')]), Element(1, 'CHAR', 'UNICODE'), Element(1, 'GEDC', [Element(2, 'VERS', '5.5'), Element(2, 'FORM', 'LINEAGE-LINKED')])]),\nIndividual(0, 'INDI', '@I1@', [Element(1, 'SEX', 'M')]),\nFamily(0, 'FAM', '@F2@'),\nElement(0, 'TRLR'))"))

    def testCanOnlyAddIndividualOrFamilyToFile(self):
        gedcomfile = gedcom.GedcomFile()
        title = gedcom.Element(tag="TITL")
        self.assertRaises(Exception, gedcomfile.add_element, (title))

    def testCanAddIndividualRaw(self):
        gedcomfile = gedcom.GedcomFile()
        element = gedcom.Element(tag="INDI")
        gedcomfile.add_element(element)

    def testCanAddFamilyRaw(self):
        gedcomfile = gedcom.GedcomFile()
        element = gedcom.Element(tag="FAM")
        gedcomfile.add_element(element)

    def testCanAddIndividualObj(self):
        gedcomfile = gedcom.GedcomFile()
        element = gedcom.Individual()
        gedcomfile.add_element(element)

    def testCanAddFamilyObj(self):
        gedcomfile = gedcom.GedcomFile()
        element = gedcom.Family()
        gedcomfile.add_element(element)

    def testIndividualIdsWork(self):
        gedcomfile = gedcom.GedcomFile()
        element1 = gedcom.Individual()
        element2 = gedcom.Individual()
        self.assertEqual(element1.id, None)
        self.assertEqual(element2.id, None)

        gedcomfile.add_element(element1)
        gedcomfile.add_element(element2)

        self.assertEqual(element1.id, '@I1@')
        self.assertEqual(element2.id, '@I2@')

    def testIdAssismentIsRobust(self):
        gedcomfile = gedcom.parse_string("0 HEAD\n0 @I1@ INDI\n1 NAME\n2 GIVN Bob\n2 SURN Cox\n\n0 TRLR")
        element1 = gedcom.Individual()
        self.assertEqual(element1.id, None)
        gedcomfile.add_element(element1)
        self.assertEqual(element1.id, '@I2@')

    def testCanAutoDetectInputFP(self):
        fp = six.StringIO(GEDCOM_FILE)
        parsed = gedcom.parse(fp)
        self.assertTrue(isinstance(parsed, gedcom.GedcomFile))

    def testCanAutoDetectInputString(self):
        parsed = gedcom.parse(GEDCOM_FILE)
        self.assertTrue(isinstance(parsed, gedcom.GedcomFile))

    def testCanAutoDetectInputFilename(self):
        myfile = tempfile.NamedTemporaryFile()
        filename = myfile.name
        parsed = gedcom.parse(filename)
        self.assertTrue(isinstance(parsed, gedcom.GedcomFile))

    def testSupportNameInGivenAndSurname(self):
        gedcomfile = gedcom.parse_string("0 HEAD\n0 @I1@ INDI\n1 NAME\n2 GIVN Bob\n2 SURN Cox\n\n0 TRLR")
        self.assertEqual(gedcomfile['@I1@'].name, ('Bob', 'Cox'))

    def testSupportNameInOneWithSlashes(self):
        gedcomfile = gedcom.parse_string("0 HEAD\n0 @I1@ INDI\n1 NAME Bob /Cox/\n\n0 TRLR")
        self.assertEqual(gedcomfile['@I1@'].name, ('Bob', 'Cox'))

    def testSaveFile(self):
        gedcomfile = gedcom.parse_string(GEDCOM_FILE)
        outputfile = tempfile.NamedTemporaryFile()
        outputfilename = outputfile.name
        gedcomfile.save(outputfile)
        outputfile.seek(0,0)
        
        self.assertEqual(outputfile.read(), GEDCOM_FILE.encode("utf8"))
        self.assertRaises(Exception, gedcomfile.save, (outputfilename))
        outputfile.close()
        
        gedcomfile.save(outputfilename)
        with open(outputfilename) as output:
            self.assertEqual(output.read(), GEDCOM_FILE)
        remove(outputfilename)

    def testErrorWithBadTag(self):
        self.assertRaises(Exception, gedcom.Individual, [], {'tag': 'FAM'})

    def testErrorWithBadLevel(self):
        individual = gedcom.Individual(level='foo')
        self.assertRaises(Exception, individual.set_levels_downward)

    def testNote(self):
        gedcomfile = gedcom.parse_string("0 HEAD\n0 @I1@ INDI\n1 NAME\n2 GIVN Bob\n2 SURN Cox\n1 NOTE foo\n0 TRLR")
        self.assertEqual(list(gedcomfile.individuals)[0].note, 'foo')

    def testNoteCont(self):
        gedcomfile = gedcom.parse_string("0 HEAD\n0 @I1@ INDI\n1 NAME\n2 GIVN Bob\n2 SURN Cox\n1 NOTE foo\n2 CONT bar\n0 TRLR")
        self.assertEqual(list(gedcomfile.individuals)[0].note, 'foo\nbar')

    def testNoteConc(self):
        gedcomfile = gedcom.parse_string("0 HEAD\n0 @I1@ INDI\n1 NAME\n2 GIVN Bob\n2 SURN Cox\n1 NOTE foo\n2 CONC bar\n0 TRLR")
        self.assertEqual(list(gedcomfile.individuals)[0].note, 'foobar')

    def testNoteError(self):
        gedcomfile = gedcom.parse_string("0 HEAD\n0 @I1@ INDI\n1 NAME\n2 GIVN Bob\n2 SURN Cox\n1 NOTE foo\n2 TITL bar\n0 TRLR")
        ind = list(gedcomfile.individuals)[0]
        self.assertRaises(ValueError, lambda : ind.note)

    def testBirth(self):
        gedcomfile = gedcom.parse_string("0 HEAD\n0 @I1@ INDI\n1 NAME\n2 GIVN Bob\n2 SURN Cox\n1 BIRT\n2 DATE 1980\n2 PLAC London\n0 TRLR")
        ind = list(gedcomfile.individuals)[0]
        birth = ind.birth
        self.assertEquals(birth.place, "London")
        self.assertEquals(birth.date, "1980")

    def testDeath(self):
        gedcomfile = gedcom.parse_string("0 HEAD\n0 @I1@ INDI\n1 NAME\n2 GIVN Bob\n2 SURN Cox\n1 DEAT\n2 DATE 1980\n2 PLAC London\n0 TRLR")
        ind = list(gedcomfile.individuals)[0]
        death = ind.death
        self.assertEquals(death.place, "London")
        self.assertEquals(death.date, "1980")

    def testSetSex(self):
        gedcomfile = gedcom.GedcomFile()
        ind = gedcomfile.individual()
        ind.set_sex('m')
        ind.set_sex('M')
        ind.set_sex('f')
        ind.set_sex('F')
        self.assertRaises(TypeError, ind.set_sex, 'foo')
        self.assertRaises(TypeError, ind.set_sex, 'female')
        self.assertRaises(TypeError, ind.set_sex, 'male')

    def testTitle(self):
        gedcomfile = gedcom.parse_string("0 HEAD\n0 @I1@ INDI\n1 NAME\n2 GIVN Bob\n2 SURN Cox\n1 TITL King\n0 TRLR")
        self.assertEqual(list(gedcomfile.individuals)[0].title, 'King')

        gedcomfile = gedcom.parse_string("0 HEAD\n0 @I1@ INDI\n1 NAME\n2 GIVN Bob\n2 SURN Cox\n0 TRLR")
        self.assertEqual(list(gedcomfile.individuals)[0].title, None)

    def testParseError(self):
        self.assertRaises(Exception, gedcom.parse_string, "foo")

    def testFirstNameOnly1(self):
        gedcomfile = gedcom.parse_string("0 HEAD\n0 @I1@ INDI\n1 NAME\n2 GIVN Bob\n0 TRLR")
        self.assertEqual(list(gedcomfile.individuals)[0].name, ('Bob', None))

    def testFirstNameOnly2(self):
        gedcomfile = gedcom.parse_string("0 HEAD\n0 @I1@ INDI\n1 NAME Bob\n0 TRLR")
        self.assertEqual(list(gedcomfile.individuals)[0].name, ('Bob', None))

    def testLastNameOnly1(self):
        gedcomfile = gedcom.parse_string("0 HEAD\n0 @I1@ INDI\n1 NAME\n2 SURN Bob\n0 TRLR")
        self.assertEqual(list(gedcomfile.individuals)[0].name, (None, 'Bob'))

    def testEmptyName(self):
        gedcomfile = gedcom.parse_string("0 HEAD\n0 @I1@ INDI\n1 NAME \n0 TRLR")
        self.assertEqual(list(gedcomfile.individuals)[0].name, (None, None))

    def testInvalidNames(self):
        gedcomfile = gedcom.parse_string("0 HEAD\n0 @I1@ INDI\n1 NAME Bob /Russel\n0 TRLR")
        self.assertRaises(Exception, lambda : list(gedcomfile.individuals)[0].name)

    #def testUnicodeUTF8(self):
    #    # FIXME decide what should happen to BOM-less 
    #    # Read up spec and check default char encoding
    #    gedcomfile = gedcom.parse_string("0 HEAD\n0 @I1@ INDI\n1 NAME B\xC3\xB6b /R\xC3\xBC\xC3\x9Fel/\n0 TRLR")
    #    self.assertEqual(list(gedcomfile.individuals)[0].name, (u'Böb', u'Rüßel'))


    def _test_encoded_with_bom(desired_encoding):
        def test(self):
            filecontent = u"0 HEAD\n0 @I1@ INDI\n1 NAME Böb /Rüßel/\n0 TRLR"
            encoded_content = filecontent.encode(desired_encoding)

            gedcomfile = gedcom.parse_string(encoded_content)
            self.assertEqual(list(gedcomfile.individuals)[0].name, (u'Böb', u'Rüßel'))

        test.__doc__ = "Should not get an exception with encoding {}".format(desired_encoding)
        return test

    # utf{16,32} always include a BOM. we want utf8 with a bom, which is utf-8-sig
    testUnicodeUTF8WithBOM = _test_encoded_with_bom("utf-8-sig")
    testUnicodeUTF16LEWithBOM = _test_encoded_with_bom("utf-16-le")
    testUnicodeUTF16BEWithBOM = _test_encoded_with_bom("utf-16-be")
    testUnicodeUTF32WithBOM = _test_encoded_with_bom("utf-32")
    testUnicodeUTF32LEWithBOM = _test_encoded_with_bom("utf-32-le")
    testUnicodeUTF32BEWithBOM = _test_encoded_with_bom("utf-32-be")

    def _test_encoded_with_head_char(char_encoding_value, desired_encoding):
        def test(self):
            filecontent = u"0 HEAD\n1 CHARACTER SET {0}\n0 @I1@ INDI\n1 NAME Böb /Rüßel/\n0 TRLR".format(char_encoding_value)
            encoded_content = filecontent.encode(desired_encoding)

            gedcomfile = gedcom.parse_string(encoded_content)
            self.assertEqual(list(gedcomfile.individuals)[0].name, (u'Böb', u'Rüßel'))

        test.__doc__ = "Should not get an exception with encoding {}".format(desired_encoding)
        return test

    testUnicodeUTF8WithHeadChar = _test_encoded_with_head_char("UTF-8", "utf8")
    testUnicodeUTF8WithHeadChar = _test_encoded_with_head_char("UNICODE", "utf16")

    def _testUnicodeCantDoAsciiWithNonAscii(self):
        # FIXME finish this
        gedcomfile = gedcom.GedcomFile()
        gedcomfile.ensure_header_trailer()
    
        gedcomfile['HEAD'].element('CHARACTER SET' , value="ASCII")

        individual = gedcomfile.individual()
        # Ensure we get a exception
        self.assertRaises(Exception, lambda: individual.set_name(u"Böb", u"Rüßel"))
        
if __name__ == '__main__':
    unittest.main()
