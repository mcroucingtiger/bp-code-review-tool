from bs4 import BeautifulSoup
import logging


class Result:
    """Result is a column in both the Object and Process report pages."""
    NO = 'No'
    YES = 'Yes'
    FREQUENTLY = 'Frequently'
    INFREQUENTLY = 'Infrequently'
    NOT_APPLICABLE = 'Not Applicable'


class ReportPage:
    """"Class to manage information within a report page.

    Categorises all error cases found into a structure of:
    ReportPage (object) > considerations (list) > consideration (dict) > errors (list) > error (dict)
    The ReportPage is converted to a dict, so the final process output can be converted to a
    JSON to be returned to the HTTP Request.

    Any methods with a BeautifulSoup parameter accept only the Tag of a single Object or Process.

    Attributes:
          considerations (list): List of considerations that have been processed for this report page
          page_type (str): 'Object','Process' or 'Settings"
          page_name (str): The name of the current Object or Process from the XML
          actions (list of str): If page is for an Object, lists out each Action contained from XML

    """

    def __init__(self):
        self.considerations = []
        self.page_type = None
        self.object_type = None
        self.page_name = None
        self.actions = []

    def set_page_header_info(self, page_type, soup: BeautifulSoup, object_type=None, evaluated=False):
        """Set the type of report page as Process/Object and gets Object's name and Actions."""
        self.page_type = page_type

        if evaluated:
            self.object_type = object_type + " (Evaluated)"
        else:
            self.object_type = object_type

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
            action_name = action.next_element.string
            if action_name != 'Clean Up':
                self.actions.append(action.next_element.string)
        logging.info("Action names from BP Object extracted")

    def set_consideration(self, consideration_name, max_score, score, result, errors, warnings):
        """Create a consideration dict containing an errors list.

        Default value is for success.
        """
        self.considerations.append({'Consideration Name': consideration_name, 'Errors': errors, 'Warnings': warnings,
                                    'Score': score, 'Max Score': max_score, 'Result': result})

    def get_page_as_dict(self) -> dict:
        """Return a dict containing the report page information, considerations and the corresponding error data"""
        return {
            "Report Page Name": self.page_name,
            "Page Type": self.page_type,
            "Object Type": self.object_type,
            "Object Actions": self.actions,
            "Report Considerations": self.considerations
        }


# Helper Functions
def error_as_dict(error_name, error_location) -> dict:
    """Create an error dict of {Error Name: ..., Error Location: ...}."""
    return {'Error Name': error_name, 'Error Location': error_location}


def warning_as_dict(warning_name, warning_location) -> dict:
    """Create an warning dict of {Warning Name: ..., Warning Location: ...}."""
    return {'Warning Name': warning_name, 'Warning Location': warning_location}

