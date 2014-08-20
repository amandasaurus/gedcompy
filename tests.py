import unittest
import gedcom

# Sample GEDCOM file from Wikipedia
GEDCOM_FILE = """
0 HEAD
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
1 NAME Bob /Cox/
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



class GedComTestCase(unittest.TestCase):

    def testCanParse(self):
        #import pudb; pudb.set_trace()
        parsed = gedcom.parse_string(GEDCOM_FILE)
        self.assertTrue(isinstance(parsed, gedcom.GedcomFile))
        
        people = list(parsed.individuals)
        self.assertTrue(len(people), 3)

        bob = people[0]
        self.assertEquals(bob.name, ("Bob", "Cox"))
        self.assertEquals(bob.sex, 'M')
        self.assertEquals(bob.gender, 'M')
        self.assertTrue(bob.is_male)
        self.assertFalse(bob.is_female)
        self.assertEquals(bob.parents, [])

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

    def testCreateEmpty(self):
        gedcomfile = gedcom.GedcomFile()
        self.assertEqual(gedcomfile.gedcom_lines_as_string(), '0 HEAD\n1 SOUR\n2 NAME gedcompy\n2 VERS 0.1.0\n1 CHAR UNICODE\n0 TRLR')


    def testCanCreate(self):
        gedcomfile = gedcom.GedcomFile()
        individual = gedcom.Individual()
        individual.set_sex("M")
        self.assertEquals(individual.level, None)
        gedcomfile.add_element(individual)

        self.assertEquals(individual.level, 0)

        self.assertEquals(list(gedcomfile.individuals)[0], individual)

        self.assertEquals(individual.tag, 'INDI')
        self.assertEquals(individual.level, 0)

        self.assertEqual(gedcomfile.gedcom_lines_as_string(), '0 HEAD\n1 SOUR\n2 NAME gedcompy\n2 VERS 0.1.0\n1 CHAR UNICODE\n0 @I1@ INDI\n1 SEX M\n0 TRLR')


        

if __name__ == '__main__':
    unittest.main()
