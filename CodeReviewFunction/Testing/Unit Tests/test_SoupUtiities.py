from unittest import TestCase
from ... import SoupUtilities
from bs4 import BeautifulSoup
import pickle


class TestExtract_soups(TestCase):
    def setUp(self):
        simple_xml_loaction = "C:/Users/MorganCrouch/Documents/Github/CodeReviewSAMProj/" \
                              "CodeReviewFunction/Testing/Fixtures/multi_process_pickled_soups.txt"
        with open(simple_xml_loaction, 'r') as file:
            self.xml = file.read()

    def test_extract_soups(self):
        sub_soups = SoupUtilities.extract_soups(self.xml)
        self.assertIsInstance(sub_soups[0], BeautifulSoup)
        self.assertTrue(sub_soups.metadata.contents[0].name == 'header')

    def test_failed_extract_soups(self):
        xml_string = ''
        sub_soups = SoupUtilities.extract_soups(xml_string)
        self.assertTrue(len(sub_soups.processes.contents) == 0)

class TestDetermine_object_type(TestCase):

    def setUp(self):
        pickled_soup_loaction = "C:/Users/MorganCrouch/Documents/Github/CodeReviewSAMProj/CodeReviewFunction/Testing" \
                                "/Fixtures/MI_Premium_pickled_soups.txt"
        with open(pickled_soup_loaction, 'rb') as file:
            soup = pickle.load(file)


        a = 2

    def test_base(self):
        self.fail()













