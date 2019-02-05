from bs4 import BeautifulSoup, Tag
import logging
import inspect
import sys
from ..ReportPage import error_as_dict, Result
from .ConsiderationAbstract import Consideration


# --- Utility functions ---
def object_consideration_module_classes() -> list:
    """Retrieve a tuple containing all consideration class names' in this module, and their metaclass'"""
    object_classes = []
    clsmembers = inspect.getmembers(sys.modules[__name__], inspect.isclass)
    irrelevant_classes = ['Consideration', 'ReportPageHelper', 'Result', 'SoupStrainer', 'Sub_Soup', 'BeautifulSoup',
                          'Tag']
    for consideration_class in clsmembers:
        if consideration_class[0] not in irrelevant_classes:
            try:
                consideration_class[1].CONSIDERATION_NAME
            except AttributeError:
                print(consideration_class[0] + " class does not have a consideration value")
            else:
                object_classes.append(consideration_class)

    return object_classes


def object_not_blacklisted(blacklist, object_soup) -> bool:
    """Check object name doesn't contain a blacklisted word.

    Most often this word is 'wrapper' as many rules that apply to base objects are not applicable to their wrapper
    objects."""
    object_name = object_soup.get('name').lower()
    if not any(blacklist_word in object_name for blacklist_word in blacklist):
        return True
    else:
        return False


def action_not_blacklisted(blacklist, action_name)->bool:
    """Check action name doesn't constain blacklisted words"""
    action_name = action_name.lower()
    if not any(blacklist_word in action_name for blacklist_word in blacklist):
        return True
    else:
        return False


def get_action_subsheets(object_soup: BeautifulSoup):
    """Get a list of touples containing (subsheetid, subsheetname) for all Actions in the object."""
    subsheets = object_soup.find_all('subsheet')
    subsheets_info = [(subsheet.get('subsheetid'), subsheet.next_element.string) for subsheet in subsheets]
    return subsheets_info


def subsheetid_to_action(stage_subsheetid, action_subsheets)->str:
    """Find the containing Action's name from a stage's subsheetid.

    action_subsheets will be the return value of the funtion get_action_subsheets().
    """
    for action_subsheet in action_subsheets:
        action_subsheet_id = action_subsheet[0]
        if action_subsheet_id == stage_subsheetid:
            action_name = action_subsheet[1]
            return action_name


# --- Object Considerations ---
class CheckObjHasAttach(Consideration):
    """"Does the Business Object have an 'Attach' Action that reads the connected status before Attaching?

    Ignores Wrapper objects."""
    CONSIDERATION_NAME = "Does the Business Object have an 'Attach' Action " \
                         "that reads the connected status before Attaching?"

    def __init__(self):
        super().__init__(self.CONSIDERATION_NAME)

    def check_consideration(self, object_soup: BeautifulSoup):
        """Go through an object and ensure at least one page contains the word 'Attach'"""
        BLACKLIST_OBJECT_NAMES = ['wrapper']
        if object_not_blacklisted(BLACKLIST_OBJECT_NAMES, object_soup):
            attach_found = False
            subsheets = object_soup.find_all('subsheet')  # Find all page names
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
        super().__init__(self.CONSIDERATION_NAME)

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
        """Calculate the consideration's score and result."""
        # Super call to deal with when a forced scale/result is given
        super().evaluate_score_and_result(forced_score_scale, forced_result)
        if not forced_score_scale and not forced_result:
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
        super().__init__(self.CONSIDERATION_NAME)

    def check_consideration(self, object_soup: BeautifulSoup) -> list:
        """Goes through all Actions to check if they start with an Attach stage."""
        # TODO: Ask Xave if close and terminate get to be skipped or are they needed?
        BLACKLIST_ACTION_NAMES = ['launch', 'close', 'terminate', 'attach', 'initialise', 'clean up', 'detach',
                                  'send key']
        BLACKLIST_OBJECT_NAMES = ['wrapper']

        start_stages = object_soup.find_all('stage', type='Start', recursive=False)
        action_pages = object_soup.find_all('subsheet', recursive=False)
        page_reference_stages = object_soup.find_all('stage', type='SubSheet')

        if object_not_blacklisted(BLACKLIST_OBJECT_NAMES, object_soup):
            # Iterate over all Actions in the Object
            for action_page in action_pages:
                action_name = action_page.next_element.string
                # Check the Action does not contain a word from the blacklist
                if action_not_blacklisted(BLACKLIST_ACTION_NAMES, action_name):
                    # Check Action starts with attach
                    if not self._action_begins_attach(action_page, start_stages, page_reference_stages):
                        self.errors.append(error_as_dict("", action_name))

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


class CheckNoActionCalledInAction(Consideration):
    CONSIDERATION_NAME = "No Actions call other published Actions?"

    def __init__(self):
        super().__init__(self.CONSIDERATION_NAME)

    def check_consideration(self, object_soup: BeautifulSoup):
        """Go through all stages in an Object and check that none are Action stages."""
        BLACKLIST_OBJECT_NAMES = ['wrapper']
        if object_not_blacklisted(BLACKLIST_OBJECT_NAMES, object_soup):
            action_stages = object_soup.find_all('stage', {'type': 'Action'})
            subsheets = object_soup.find_all('subsheet')
            if action_stages:
                # Goes through all found Action stages and gets their subsheetid location
                for action_stage in action_stages:
                    if action_stage.next_element.name == 'subsheetid':
                        action_subsheetid = action_stage.next_element.string
                        # Find the subsheet name from the subsheetid
                        for subsheet in subsheets:
                            if subsheet.get('subsheetid') == action_subsheetid:
                                location = subsheet.next_element.string
                                self.errors.append(error_as_dict(action_stage.get('name'), location))
                                break
                    else:
                        print("Unable to find Action's subsheet id")

    def evaluate_score_and_result(self, forced_score_scale=None, forced_result=None):
        """Calculate the consideration's score and result."""
        # Super call to deal with when a forced scale/result is given
        super().evaluate_score_and_result(forced_score_scale, forced_result)
        if not forced_score_scale and not forced_result:
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


class CheckActionsDocumentation(Consideration):
    CONSIDERATION_NAME = "Are Action descriptions, Pre-Conditions, Post Conditions, Input params & " \
                         "Output params documented to create a meaningful BOD?"

    def __init__(self):
        super().__init__(self.CONSIDERATION_NAME)

    def check_consideration(self, object_soup: BeautifulSoup):
        BLACKLIST_ACTION_NAMES = ['attach', 'initialise', 'clean up', 'detach']
        start_stages = object_soup.find_all('stage', type='Start')
        end_stages = object_soup.find_all('stage', type='End')
        action_subsheets = get_action_subsheets(object_soup)  # return list of tuple (id, name)

        # Find Subsheet Descriptions
        subsheet_info_stages = object_soup.find_all('stage', type='SubSheetInfo')
        for subsheet_info_stage in subsheet_info_stages:
            action_description = subsheet_info_stage.narrative.string
            if action_description is None:
                # Match the description stage with the Actions name and record the error
                action_name = subsheet_info_stage.get('name')
                if action_not_blacklisted(BLACKLIST_ACTION_NAMES, action_name):
                    self.errors.append(error_as_dict("Action Description", action_name))

        # Find input and output param descriptions
        for start_stage in start_stages:
            if start_stage.inputs:
                for input_param in start_stage.inputs.contents:
                    if isinstance(input_param, Tag):
                        if not input_param.get('narrative'):
                            param_name = input_param.get('name')
                            start_stage_id = start_stage.subsheetid.string
                            action_name = subsheetid_to_action(start_stage_id, action_subsheets)
                            # print(param_name + ' - ' + action_name)
                            self.errors.append(error_as_dict("Input param: " + param_name, action_name))

        for end_stage in end_stages:
            if end_stage.outputs:
                for output_param in end_stage.outputs.contents:
                    if isinstance(output_param, Tag):
                        if not output_param.get('narrative'):
                            param_name = output_param.get('name')
                            end_stage_id = end_stage.subsheetid.string
                            action_name = subsheetid_to_action(end_stage_id, action_subsheets)
                            self.errors.append(error_as_dict("Output param: " + param_name, action_name))

        # Find pre and post conditions
        for start_stage in start_stages:
            if start_stage.subsheetid:  # Initialize's Start doesn't have subsheetid
                action_name = subsheetid_to_action(start_stage.subsheetid.string, action_subsheets)
                if action_not_blacklisted(BLACKLIST_ACTION_NAMES, action_name):
                    conditions_documented = True
                    error_str = ""

                    if start_stage.preconditions is None:
                        conditions_documented = False
                        error_str += "No Precondition"

                    if start_stage.postconditions is None:
                        conditions_documented = False
                        if len(error_str) > 5:  # "No Precondition"
                            error_str += " or Postcondition"
                        else:
                            error_str += "No Postcondition"

                    if not conditions_documented:
                        self.errors.append(error_as_dict(error_str, action_name))


    def evaluate_score_and_result(self, forced_score_scale=None, forced_result=None):
        """Calculate the consideration's score and result."""
        # Super call to deal with when a forced scale/result is given
        super().evaluate_score_and_result(forced_score_scale, forced_result)
        if not forced_score_scale and not forced_result:
            if self.errors:
                if len(self.errors) <= 3:
                    self.score = self.max_score * 0.7
                    self.result = Result.FREQUENTLY
                elif 2 <= len(self.errors) <= 6:
                    self.score = self.max_score * 0.3
                    self.result = Result.INFREQUENTLY
                else:
                    self.score = 0
                    self.result = Result.NO


class CheckGlobalTimeoutUsedWaits(Consideration):
    CONSIDERATION_NAME = "Global variable enable a quick change to timeout values when application " \
                         "behaviour dictates."

    def __init__(self):
        super().__init__(self.CONSIDERATION_NAME)

    def check_consideration(self, object_soup: BeautifulSoup):
        BLACKLIST_ACTION_NAMES = ['attach', 'initialise', 'clean up', 'detach']
        data_stages = object_soup.find_all('stage', type='Data')
        for data_stage in data_stages:
            if data_stage.subsheetid is None:  # Any stages (inc Data Items) on the init page have no subsheetid
                print(data_stage.get('name'))



    def evaluate_score_and_result(self, forced_score_scale=None, forced_result=None):
        """Calculate the consideration's score and result."""
        # Super call to deal with when a forced scale/result is given
        super().evaluate_score_and_result(forced_score_scale, forced_result)
        if not forced_score_scale and not forced_result:
            if self.errors:
                if len(self.errors) <= 3:
                    self.score = self.max_score * 0.7
                    self.result = Result.FREQUENTLY
                elif 2 <= len(self.errors) <= 6:
                    self.score = self.max_score * 0.3
                    self.result = Result.INFREQUENTLY
                else:
                    self.score = 0
                    self.result = Result.NO


