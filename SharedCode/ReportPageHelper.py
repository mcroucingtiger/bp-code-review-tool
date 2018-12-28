from bs4 import BeautifulSoup
import logging


class Result:
    """Result is a column in both the Object and Process report page.

    This Class is similar to an enum, to help clarify their use as parameters
    """
    NO = 'No'
    YES = 'Yes'
    FREQUENTLY = 'Frequently'
    INFREQUENTLY = 'Infrequently'
    NOT_APPLICABLE = 'Not Applicable'


class ReportPageHelper:
    """"Helper class to manage a report page.

    Categorises all error cases found into a structure of:
    considerations (list) > consideration (dict) > errors (list) > error (dict)
    and outputs a JSON to be returned to the HTTP Request.

    Any methods with a Beautiful Soup parameter accept only the tag of a single Object or Process.

    Attributes:
          considerations (list): List of considerations that have been processed for this report page
          page_type (str): 'Object' or 'Process'
          page_name (str): The name of the current Object or Process from the XML
          actions (list of str): If page is for an Object, lists out each Action contained from XML

    """

    def __init__(self):
        self.considerations = []
        self.page_type = None
        self.page_name = None
        self.actions = []

    def set_page_type(self, page_type, soup: BeautifulSoup):
        """Set the type of report page as Process or Object and gets Object's Actions """
        self.page_type = page_type

        if page_type == 'Process':
            self._set_page_name(soup)
        elif page_type == 'Object':
            self._set_page_name(soup)
            self._set_actions(soup)

    def _set_page_name(self, soup: BeautifulSoup):
        """Set the page name as the name of the current BP Process or Object"""
        self.page_name = soup.get('name')
        logging.info("Setting report page details for: " + self.page_name)

    def _set_actions(self, object_soup: BeautifulSoup):
        """Go through a Beautiful Soup of a single BP Object's XML and extracts all Action names"""
        actions = object_soup.find_all("subsheet")
        for action in actions:
            self.actions.append(action.next_element.string)
        logging.info("Action names from BP Object extracted")

    def set_error(self, consideration_name, error: dict):
        """Add the error to the relevant topic and consideration"""
        for consideration in self.considerations:
            if consideration["Consideration Name"] == consideration_name:  # Checking consideration list
                consideration['Errors'].append(error)
                break

    def set_consideration(self, consideration_name, max_score):
        """Create a consideration dict containing an errors list.

        Default value is for success."""
        self.considerations.append({'Consideration Name': consideration_name, 'Errors': [],
                                    'Max Score': max_score, 'Score': 10, 'Result': "Yes"})

    def set_consideration_score(self, consideration_name, score, result):
        """Set the consideration result if there are any error cases"""
        for consideration in self.considerations:
            if consideration["Consideration Name"] == consideration_name:
                consideration['Score'] = score
                consideration['Result'] = result

    def get_report_page(self) -> dict:
        """Return a dict containing the report page information, considerations and their corresponding error data"""
        return {
            "Report Page Name": self.page_name,
            "Page Type": self.page_type,
            "Object Actions": self.actions,
            "Report Considerations": self.considerations
        }


def error_as_dict(error_name, error_location) -> dict:
    """Create error dict"""
    return {'Error Name': error_name, 'Error Location': error_location}

