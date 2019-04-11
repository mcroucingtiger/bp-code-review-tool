from bs4 import BeautifulSoup
import logging

class ReportPage:
    """"Class to manage information within a single report page.

    The data structure of a report page:
    ReportPage (object) > considerations (list) > consideration (dict) > errors (list) > error (dict)
    The ReportPage is converted to a dict, so the final process output can be converted to a
    JSON to be returned to the HTTP Request.

    Attributes:
          considerations (list): List of considerations that have been processed for this report page
          page_type (str): 'Object','Process' or 'Settings".
          page_name (str): The name of the current Object or Process from the XML.
          object_type (str): 'Wrapper' or 'Base'. May have a suffix of '(evaluated)'.
          object_actions (list of str): If page is for an Object, lists out each BP Action contained.

    """

    def __init__(self, page_name, page_type, object_type=None, object_actions=None):
        self.considerations = []
        self.page_name = page_name
        self.page_type = page_type
        self.object_type = object_type
        self.actions = object_actions

    def set_consideration(self, consideration):
        """Create a consideration dict containing and add it to the considerations list of the current Report Page.

        :param consideration: (Consideration) A single consideration object.
        """
        self.considerations.append({'Consideration Name': consideration.CONSIDERATION_NAME,
                                    'Errors': consideration.errors_list,
                                    'Warnings': consideration.warning_list,
                                    'Score': consideration.score,
                                    'Max Score': consideration.max_score,
                                    'Result': consideration.result})

    def get_page_as_dict(self) -> dict:
        """Return a dict containing the report page information, considerations and the corresponding error data."""
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


class Result:
    """Result is a column in both the Object and Process report pages."""
    NO = 'No'
    YES = 'Yes'
    FREQUENTLY = 'Frequently'
    INFREQUENTLY = 'Infrequently'
    NOT_APPLICABLE = 'Not Applicable'

