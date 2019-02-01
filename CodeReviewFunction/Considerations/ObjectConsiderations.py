from bs4 import BeautifulSoup
import logging
import inspect
import sys
from ..ReportPage import error_as_dict, Result
from .ConsiderationAbstract import Consideration


def object_consideration_module_classes() -> list:
    """Retrieve a tuple containing all consideration class names' in this module, and their metaclass'"""
    object_classes = []
    clsmembers = inspect.getmembers(sys.modules[__name__], inspect.isclass)
    irrelevant_classes = ['Consideration', 'ReportPageHelper', 'Result', 'SoupStrainer', 'Sub_Soup', 'BeautifulSoup']
    for consideration_class in clsmembers:
        if consideration_class[0] not in irrelevant_classes:
            try:
                consideration_class[1].CONSIDERATION_NAME
            except AttributeError:
                print(consideration_class[0] + " class does not have a consideration value")
            else:
                object_classes.append(consideration_class)

    return object_classes


class CheckObjHasAttach(Consideration):
    """Does the Business Object have an 'Attach' Action"""
    CONSIDERATION_NAME = "Does the Business Object have an 'Attach' Action " \
                         "that reads the connected status before Attaching?"

    def __init__(self):
        super().__init__(CheckObjHasAttach.CONSIDERATION_NAME)

    def check_consideration(self, soup: BeautifulSoup) -> list:
        """Go through an object and ensure at least one page contains the word 'Attach'"""
        attach_found = False
        subsheets = soup.find_all('subsheet')  # Find all page names
        for subsheet in subsheets:
            if subsheet.next_element.string.lower().find("attach") >= 0:  # A page has the work 'Attach' in it
                attach_found = True
                # TODO: SOON - Ensure this page also has a read attached stage (maybe)
                break

        if not attach_found:
            self.errors.append(error_as_dict("Unable to find and an Attach page within the Object", "N/A"))


class CheckExceptionDetails(Consideration):
    """Do all Exception stages have an exception detail?"""
    CONSIDERATION_NAME = "Do all Exception stages have an exception detail?"

    def __init__(self):
        super().__init__(CheckExceptionDetails.CONSIDERATION_NAME)

    def check_consideration(self, soup: BeautifulSoup) -> list:
        """Find all exception stages with empty an exception detail field and store them within the self.errors list"""
        logging.info("'CheckExceptionDetail method called")
        exception_stages = soup.find_all('exception')
        for exception_stage in exception_stages:
            if not exception_stage.get('detail') and not exception_stage.get(
                    'usecurrent'):  # No detail and not preserve
                exception_name = exception_stage.parent.get('name')
                parent_subsheet_id = exception_stage.parent.subsheetid.string
                exception_page = soup.find('subsheet', {'subsheetid': parent_subsheet_id}).next_element.string

                self.errors.append(error_as_dict(exception_name, exception_page))

    def evaluate_score_and_result(self, forced_score_scale=None, forced_result=None):
        """Calculate the consideration's score and result. Default value is hard fail {score: 0, result: No}."""
        # TODO: Check this super call works as expected
        # Super call to deal with when a forced scale/result is given
        super().evaluate_score_and_result(forced_score_scale, forced_result)

        if self.errors:
            if len(self.errors) < 2:
                self.score = self.max_score * 0.7
                self.result = Result.FREQUENTLY
            elif 2 <= len(self.errors) <= 4:
                self.score = self.max_score * 0.3
                self.result = Result.INFREQUENTLY
            else:
                self.score = 0
                self.result = Result.NO


class CheckActionsUseAttach(Consideration):
    CONSIDERATION_NAME = "Do all Actions use the Attach action?"

    def __init__(self):
        super().__init__(CheckActionsUseAttach.CONSIDERATION_NAME)

    def check_consideration(self, soup: BeautifulSoup) -> list:
        """Goes through all Actions to check if they start with an Attach stage.

        Exceptions for ....

        """
        ...


