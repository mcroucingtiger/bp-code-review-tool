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
    """"Does the Business Object have an 'Attach' Action that reads the connected status before Attaching?

    Ignores Wrapper objects."""
    CONSIDERATION_NAME = "Does the Business Object have an 'Attach' Action " \
                         "that reads the connected status before Attaching?"

    # TODO: ignore wrapper obejcts (refer to uses attach)

    def __init__(self):
        super().__init__(CheckObjHasAttach.CONSIDERATION_NAME)

    def check_consideration(self, soup: BeautifulSoup):
        """Go through an object and ensure at least one page contains the word 'Attach'"""
        attach_found = False
        subsheets = soup.find_all('subsheet')  # Find all page names
        for subsheet in subsheets:
            if subsheet.next_element.string.lower().find("attach") >= 0:  # A page has the work 'Attach' in it
                attach_found = True
                # TODO: Ensure this page also has a read attached stage (maybe)
                break

        if not attach_found:
            self.errors.append(error_as_dict("Unable to find and an Attach page within the Object", "N/A"))


class CheckExceptionDetails(Consideration):
    """Do all Exception stages have an exception detail?"""
    CONSIDERATION_NAME = "Do all Exception stages have an exception detail?"

    def __init__(self):
        super().__init__(CheckExceptionDetails.CONSIDERATION_NAME)

    def check_consideration(self, soup: BeautifulSoup):
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
            if len(self.errors) <= 1:
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

    def check_consideration(self, object_soup: BeautifulSoup) -> list:
        """Goes through all Actions to check if they start with an Attach stage."""
        # TODO: Ask Xave if close and terminate get to be skipped or are they needed?
        BLACKLIST_ACTION_NAMES = ['launch', 'close', 'terminate', 'attach', 'initialise', 'clean up', 'detach',
                                  'send key']
        BLACKLIST_OBJECT_NAMES = ['wrapper']

        object_name = object_soup.get('name').lower()
        start_stages = object_soup.find_all('stage', type='Start', recursive=False)
        action_pages = object_soup.find_all('subsheet', recursive=False)
        page_reference_stages = object_soup.find_all('stage', type='SubSheet')

        # Current Object name not blacklisted
        if not any(blacklist_word in object_name for blacklist_word in BLACKLIST_OBJECT_NAMES):
            # Iterate over all Actions in the Object
            for action_page in action_pages:
                action_name = action_page.next_element.string.lower()
                # Check the Action does not contain a word from the blacklist
                if not any(blacklist_word in action_name for blacklist_word in BLACKLIST_ACTION_NAMES):
                    # Check Action starts with attach
                    if not self._action_begins_attach(action_page, start_stages, page_reference_stages):
                        self.errors.append(error_as_dict("", action_page.next_element.string))

    @staticmethod
    def _action_begins_attach(action_page, start_stages, page_reference_stages):
        """Return True if an Action's page starts with an Attach page stage"""
        subsheet_id = action_page.get('subsheetid')
        # Gets all start stages in the object
        for start_stage in start_stages:
            # Finds the start stage of the current Action
            if start_stage.next_element.string == subsheet_id:
                start_onsuccess = start_stage.find('onsuccess').string
                for page_reference_stage in page_reference_stages:
                    # Check if a Page reference stage is the first step in the Action after start stage
                    if page_reference_stage.get('stageid') == start_onsuccess:
                        if 'attach' in page_reference_stage.get('name').lower():
                            return True
        return False
