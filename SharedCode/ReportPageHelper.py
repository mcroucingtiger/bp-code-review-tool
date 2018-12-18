import json
from bs4 import BeautifulSoup
import logging


class ReportPageHelper:
    """"
    Helper class to categorise all error cases found into a structure of:
    considerations (list) > consideration (dict) > errors (list) > error (dict)
    and output a JSON to be returned to the HTTP Request.

    Any methods with a Beautiful Soup parameter accept only the tag of a single Object or Process
    """
    def __init__(self):
        self.considerations = []
        self.page_type = None
        self.page_name = None
        self.actions = []

    def set_page_type(self, page_type, soup: BeautifulSoup):
        """Sets the type of report page (Process or Object)"""
        self.page_type = page_type

        if page_type == 'Process':
            self._set_page_name(soup)

        elif page_type == 'Object':
            self._set_page_name(soup)
            self._set_actions(soup)

    def _set_page_name(self, soup: BeautifulSoup):
        """Sets the page name as the name of the current BP Process or Object"""
        self.page_name = soup.get('name')
        logging.info("Setting report page details for: " + self.page_name)

    def _set_actions(self, object_soup: BeautifulSoup):
        """Goes through a Beautiful Soup of a single BP Object's XML and extracts all Action names"""
        actions = object_soup.find_all("subsheet")
        for action in actions:
            self.actions.append(action.next_element.string)
        logging.info("Action names from BP Object extracted")

    def set_error(self, consideration_name, error_name, error_location):
        """Adds the error to the relevant topic and consideration"""
        error = {'Error': error_name, 'Error Location': error_location}
        for consideration in self.considerations:
            if consideration["Consideration Name"] == consideration_name:  # Checking consideration list
                consideration['Errors'].append(error)
                break

    def set_consideration(self, consideration_name):
        """Creates a consideration dict containing an errors list"""
        self.considerations.append({"Consideration Name": consideration_name, "Errors": []})

    def get_report_page(self) -> dict:
        """Returns a dict containing the report page information, considerations and their corresponding error data"""
        return {
            "Report Page Name": self.page_name,
            "Page Type": self.page_type,
            "Object Actions": self.actions,
            "Report Considerations": self.considerations
        }
