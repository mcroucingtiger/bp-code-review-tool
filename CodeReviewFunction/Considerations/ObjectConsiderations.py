from bs4 import BeautifulSoup, Tag
import logging
import inspect
import sys
from ..ReportPage import error_as_dict, warning_as_dict, Result
from .ConsiderationAbstract import Consideration
from .. import Settings


# --- Utility functions ---
def object_consideration_module_classes() -> list:
    """Retrieve a tuple containing all consideration class names' in this module, and their metaclass."""
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
    """Check action name doesn't constain blacklisted words."""
    action_name = action_name.lower()
    if not any(blacklist_word in action_name for blacklist_word in blacklist):
        return True
    else:
        return False


def get_action_subsheets(object_soup: BeautifulSoup):
    """Get a list of touples containing (subsheetid, subsheetname) for all Actions in the object."""
    subsheets = object_soup.find_all('subsheet', recursive=False)
    subsheets_info = [(subsheet.get('subsheetid'), subsheet.next_element.string) for subsheet in subsheets]
    return subsheets_info


def get_onsuccess_tag(stage: Tag, object_soup: BeautifulSoup) -> Tag:
    if stage.onsuccess:
        onsuccess = stage.onsuccess.string
        success_stage = object_soup.find('stage', stageid=onsuccess, recursive=False)
        return success_stage


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
# Topic: Documentation
class CheckActionsDocumentation(Consideration):
    """Pre/Post conditions are only required for Base Objects.

    If either is not found in a Wrapper, it is flagged as a Warning.
    """
    CONSIDERATION_NAME = "Are Action descriptions, Pre-Conditions, Post Conditions, Input params & " \
                         "Output params documented to create a meaningful BOD?"
    #Settings
    PASS_HURDLE = 0
    FREQUENTLY_HURDLE = 3
    INFREQUENTLY_HURDLE = 6
    MAX_ERROR_SCORE = 5

    def __init__(self): super().__init__(self.MAX_ERROR_SCORE)

    def check_consideration(self, soup: BeautifulSoup, metadata):
        BLACKLIST_ACTION_NAMES = ['attach', 'initialise', 'clean up', 'detach']
        start_stages = soup.find_all('stage', type='Start', recursive=False)
        end_stages = soup.find_all('stage', type='End', recursive=False)
        action_subsheets = get_action_subsheets(soup)  # return list of tuple (id, name)

        # Find Subsheet Descriptions
        subsheet_info_stages = soup.find_all('stage', type='SubSheetInfo')
        for subsheet_info_stage in subsheet_info_stages:
            action_description = subsheet_info_stage.narrative.string
            if action_description is None:
                # Match the description stage with the Actions name and record the error
                action_name = subsheet_info_stage.get('name')
                if action_not_blacklisted(BLACKLIST_ACTION_NAMES, action_name):
                    self.errors_list.append(error_as_dict("Action Description", action_name))

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
                            self.errors_list.append(error_as_dict("Input param: " + param_name, action_name))

        for end_stage in end_stages:
            if end_stage.outputs:
                for output_param in end_stage.outputs.contents:
                    if isinstance(output_param, Tag):
                        if not output_param.get('narrative'):
                            param_name = output_param.get('name')
                            end_stage_id = end_stage.subsheetid.string
                            action_name = subsheetid_to_action(end_stage_id, action_subsheets)
                            self.errors_list.append(error_as_dict("Output param: " + param_name, action_name))

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
                        # If the Object is a Wrapper, flag a warning. If it's a Base Object, flag as an error
                        if Settings.OBJECT_TYPES['wrapper'] in metadata['object type']:
                            error_str += ' in Wrapper'
                            self.warning_list.append(warning_as_dict(error_str, action_name))
                        else:
                            self.errors_list.append(error_as_dict(error_str, action_name))

# Topic: Exposure
class CheckObjectExposureValid(Consideration):
    """Check the current Object exposure is valid.

    Checks to see if an application model exists. If one does, then checks the Object's exposure type. If it is using
    an application model, then the Object must be interacting with the UI. Therefore the exposure should not be set
    to Background
    """
    CONSIDERATION_NAME = "Are the Business Object exposures valid?"

    def __init__(self): super().__init__()

    def check_consideration(self, soup: BeautifulSoup, metadata):
        object_run_mode = soup.get('runmode')
        application_modeller = soup.find('appdef', recursive=False)
        inherits_app_model = soup.find('parentobject', recursive=False)
        # apptypeinfo only exists after running the App Modeller Wizard
        if application_modeller.apptypeinfo or inherits_app_model:
            if object_run_mode == 'Background':
                error_str = "Application Model exists for Object with Exposure set to Background"
                self.errors_list.append(error_as_dict(error_str, "N/A"))


# Topic: Use of Attach
class CheckObjHasAttach(Consideration):
    """"Does the Business Object have an 'Attach' Action that reads the connected status before Attaching?

    Ignores Wrapper objects.
    """
    CONSIDERATION_NAME = "Does the Business Object have an 'Attach' Action " \
                         "that reads the connected status before Attaching?"

    def __init__(self): super().__init__()

    def check_consideration(self, soup: BeautifulSoup, metadata):
        """Go through an object and ensure at least one page contains the word 'Attach'."""
        # Wrapper Objects do not require an Attach
        if metadata['object type'] != Settings.OBJECT_TYPES['wrapper']:
            attach_found = False
            subsheets = soup.find_all('subsheet', recursive=False)  # Find all page names
            for subsheet in subsheets:
                if subsheet.next_element.string.lower().find("attach") >= 0:  # A page has the word 'Attach' in it
                    attach_found = True
                    # TODO: Ensure this page also has a read attached stage (maybe)
                    break

            if not attach_found:
                self.errors_list.append(error_as_dict("Unable to find and an Attach page within the Object", "N/A"))


class CheckActionsUseAttach(Consideration):
    CONSIDERATION_NAME = "Do all Actions use the Attach action?"
    # Settings
    PASS_HURDLE = 0
    FREQUENTLY_HURDLE = 2
    INFREQUENTLY_HURDLE = 3

    def __init__(self): super().__init__()

    def check_consideration(self, soup: BeautifulSoup, metadata) -> list:
        """Goes through all Actions to check if they start with an Attach stage."""
        # TODO: Ask Xave if close and terminate get to be skipped or are they needed?
        BLACKLIST_ACTION_NAMES = ['launch', 'close', 'terminate', 'attach', 'initialise', 'clean up', 'detach',
                                  'send key']

        start_stages = soup.find_all('stage', type='Start', recursive=False)
        action_pages = soup.find_all('subsheet', recursive=False)
        page_reference_stages = soup.find_all('stage', type='SubSheet')

        # Wrapper Actions do not require an Attach as the first stage as each contained Action will have an Attach
        if metadata['object type'] != Settings.OBJECT_TYPES['wrapper']:
            for action_page in action_pages:
                action_name = action_page.next_element.string
                # Check the Action does not contain a word from the blacklist
                if action_not_blacklisted(BLACKLIST_ACTION_NAMES, action_name):
                    # Check Action starts with attach
                    if not self._action_begins_attach(action_page, start_stages, page_reference_stages):
                        self.errors_list.append(error_as_dict("", action_name))

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


# Topic: Correct use of Wait Stages
class CheckActionStartWait(Consideration):
    CONSIDERATION_NAME = "Does each action start with a Wait Stage to verify " \
                         "the application is in the correct state?"

    def __init__(self):
        super().__init__()

    def check_consideration(self, soup: BeautifulSoup, metadata):
        """Check if each Action starts with an Attach page reference followed by a Wait 'Check Exists' stage."""
        BLACKLIST_ACTION_NAMES = ['launch', 'close', 'terminate', 'attach', 'initialise', 'clean up', 'detach',
                                  'send key']

        action_pages = soup.find_all('subsheet', recursive=False)
        start_stages = soup.find_all('stage', type='Start', recursive=False)

        # Wrapper Actions do not require an Attach as the first stage as each contained Action will have an Attach
        if metadata['object type'] != Settings.OBJECT_TYPES['wrapper']:
            # Iterate over all Actions in the Object
            for action_page in action_pages:
                action_name = action_page.next_element.string
                if action_not_blacklisted(BLACKLIST_ACTION_NAMES, action_name):
                    action_subsheet_id = action_page.get('subsheetid')
                    # Goes through all start stages in the Object
                    for start_stage in start_stages:
                        # Finds the start stage of the current Action
                        if start_stage.subsheetid:
                            if start_stage.subsheetid.string == action_subsheet_id:
                                success_stage = get_onsuccess_tag(start_stage, soup)
                                if success_stage.get('type') == 'SubSheet':  # Next stage a subsheet (Attach)
                                    success_stage = get_onsuccess_tag(success_stage, soup)
                                    if success_stage.get('type') == 'WaitStart':  # Following stage a Wait
                                        if len(success_stage.choices.contents) > 0:  # Wait has conditions
                                            check_exists = False
                                            for choice in success_stage.choices.contents:
                                                choice = choice.condition.id.string
                                                if 'exists' in choice.lower():
                                                    check_exists = True
                                                    break
                                            if not check_exists:
                                                error_str = "Wait stage following Attach, but no 'Check Exists'"
                                                self.errors_list.append(error_as_dict(error_str, action_name))
                                                print("**** CHECK OUT - Haven't tested ***" + error_str)
                                        else:
                                            error_str = "Wait stage following Attach has no conditions"
                                            self.errors_list.append(error_as_dict(error_str, action_name))
                                    else:
                                        error_str = "Attach page not followed by a Wait stage"
                                        self.errors_list.append(error_as_dict(error_str, action_name))
                                else:
                                    error_str = 'Action doesnt start with Attach'
                                    self.errors_list.append(error_as_dict(error_str, action_name))

    def evaluate_score_and_result(self, forced_score_scale=None, forced_result=None):
        """Calculate the consideration's score and result."""
        # Super call to deal with when a forced scale/result is given
        super().evaluate_score_and_result(forced_score_scale, forced_result)
        if not forced_score_scale and not forced_result:
            # Hard fail if no global timeout data items created
            for error_dict in self.errors_list:
                if "No global timeout data items" in error_dict.values():
                    self.score = 0
                    self.result = Result.NO
                    return

            if self.errors_list:
                if len(self.errors_list) <= 1:
                    self.score = self.max_score * 0.7
                    self.result = Result.FREQUENTLY
                elif 2 <= len(self.errors_list) <= 4:
                    self.score = self.max_score * 0.3
                    self.result = Result.INFREQUENTLY
                else:
                    self.score = 0
                    self.result = Result.NO


class CheckGlobalTimeoutUsedWaits(Consideration):
    """Checks that Global timeout data items exist on the Initialise page and ensure that they are used for
    all Wait stages within the Object.
    """
    CONSIDERATION_NAME = "Global variable enable a quick change to timeout values when application " \
                         "behaviour dictates."
    # Settings
    PASS_HURDLE = 0
    FREQUENTLY_HURDLE = 3
    INFREQUENTLY_HURDLE = 6

    def __init__(self): super().__init__()

    def check_consideration(self, soup: BeautifulSoup, metadata):
        # Don't check wait stages if Surface Automation used
        if metadata['additional info']['Surface Automation Used?'] == 'TRUE':
            return

        data_stages = soup.find_all('stage', type='Data')
        wait_stages = soup.find_all('stage', type='WaitStart')

        init_data_items = []
        for data_stage in data_stages:
            if data_stage.subsheetid is None:  # Any stages on the init page have no subsheetid
                init_data_items.append(data_stage.get('name'))

        if not init_data_items:
            self.errors_list.append(error_as_dict("No global timeout data items", "Initialise"))
            return

        for wait_stage in wait_stages:
            timeout = wait_stage.timeout.string
            if not any(init_data_item in timeout for init_data_item in init_data_items):
                action_subsheets = get_action_subsheets(soup)
                action_name = subsheetid_to_action(wait_stage.subsheetid.string, action_subsheets)
                wait_stage_name = wait_stage.get('name')
                error_string = "Wait stage '{}' has timeout value: {}".format(wait_stage_name, timeout, action_name)
                self.errors_list.append(error_as_dict(error_string, action_name))


class CheckWaitUsesDataItem(Consideration):
    CONSIDERATION_NAME = "Do Wait Stages have conditions (i.e. not arbitrary)? " \
                         "Do not include Arbitrary Waits if used for Surface Automation purposes only?"
    # Settings
    PASS_HURDLE = 0
    FREQUENTLY_HURDLE = 1
    INFREQUENTLY_HURDLE = 4

    def __init__(self): super().__init__()

    def check_consideration(self, soup: BeautifulSoup, metadata):
        """Check that all Wait stages have at least one condition (no arbitrary Waits).

        If 'Surface Automation Used?' in the configuration settings form is TRUE, this check will be ignored.
        """
        # Don't check wait stages if Surface Automation used
        if metadata['additional info']['Surface Automation Used?'] == 'TRUE':
            return
        action_subsheets = None
        wait_stages = soup.find_all('stage', type='WaitStart')
        for wait_stage in wait_stages:
            if len(wait_stage.choices) == 0:
                if not action_subsheets:
                    action_subsheets = get_action_subsheets(soup)
                action_name = subsheetid_to_action(wait_stage.subsheetid.string, action_subsheets)
                error_str = "Wait stage has no condition: '{}'".format(wait_stage.get('name'))
                self.errors_list.append(error_as_dict(error_str, action_name))


class CheckWaitTimeoutToException(Consideration):
    """Checks if a Wait stage times out to an Exception or End stage.

    It will allow a single Calc stage before either the Exception or the End to pass on information from the Object.
    If a Wait stage times out to an Anchor stage, it will keep following the successive anchors until it reaches
    a non-anchor stage.
    """
    CONSIDERATION_NAME = "Do Wait Stages timeout to an exception?"
    # Settings
    PASS_HURDLE = 0
    FREQUENTLY_HURDLE = 3
    INFREQUENTLY_HURDLE = 7

    def __init__(self): super().__init__()

    def check_consideration(self, soup: BeautifulSoup, metadata):
        wait_end_stages = soup.find_all('stage', type='WaitEnd', recursive=False)
        exception_stages = soup.find_all('stage', type='Exception', recursive=False)
        end_stages = soup.find_all('stage', type='End', recursive=False)
        calc_stages = soup.find_all('stage', type='Calculation', recursive=False)

        # Extracting the End and Exception stage id's as its faster to check the onsuccess against a python list
        # rather then searching through the full bs4 soup for a the next stage
        exception_stage_ids = []
        for exception_stage in exception_stages:
            exception_stage_ids.append(exception_stage.get('stageid'))

        end_stage_ids = []
        for end_stage in end_stages:
            end_stage_ids.append(end_stage.get('stageid'))

        calc_stage_ids = []
        for calc_stage in calc_stages:
            calc_stage_ids.append(calc_stage.get('stageid'))

        for wait_end_stage in wait_end_stages:
            onsucccess_id = wait_end_stage.onsuccess
            previously_found_calc = False
            if onsucccess_id:
                # This will follow Anchor stages until an end stage is found
                while True:
                    # Check next stage isn't an Exception stage
                    if not any(exception_id in onsucccess_id.string for exception_id in exception_stage_ids):
                        # Check next isn't an End stage
                        if not any(end_id in onsucccess_id.string for end_id in end_stage_ids):
                            # Check next is a Calc stage
                            if any(calc_id in onsucccess_id.string for calc_id in calc_stage_ids):
                                if not previously_found_calc:
                                    previously_found_calc = True
                                else:
                                    # Second calc after found so fail
                                    onsuccess_type = 'Calculation'
                                    break
                            onsuccess_stage = soup.find('stage', stageid=onsucccess_id.string, recursive=False)
                            onsuccess_type = onsuccess_stage.get('type')
                            onsucccess_id = onsuccess_stage.onsuccess
                            if onsuccess_type not in ['Anchor', 'Calculation']:
                                break
                        else:
                            onsuccess_type = 'End'
                            break
                    else:
                        onsuccess_type = 'Exception'
                        break

                if not (onsuccess_type == 'End' or onsuccess_type == 'Exception'):
                    wait_name = wait_end_stage.get('name')
                    action_subsheets = get_action_subsheets(soup)
                    action_name = subsheetid_to_action(wait_end_stage.subsheetid.string, action_subsheets)
                    error_str = "'{}' timed out to a {} stage".format(wait_name, onsuccess_type)
                    self.errors_list.append(error_as_dict(error_str, action_name))

            else:
                wait_name = wait_end_stage.get('name')
                action_subsheets = get_action_subsheets(soup)
                action_name = subsheetid_to_action(wait_end_stage.subsheetid.string, action_subsheets)
                error_str = "'{}' timeout has no connection".format(wait_name)
                self.errors_list.append(error_as_dict(error_str, action_name))


# Topic: Action Size
class CheckNoActionCalledInAction(Consideration):
    CONSIDERATION_NAME = "No Actions call other published Actions?"
    # Settings
    PASS_HURDLE = 0
    FREQUENTLY_HURDLE = 1
    INFREQUENTLY_HURDLE = 4

    def __init__(self): super().__init__()

    def check_consideration(self, soup: BeautifulSoup, metadata):
        """Go through all stages in an Object and check that none are Action stages.

        Wrapper objects and Surface Automation Base objects are allowed to call Actions. Will show uses of the
        'Sleep' Action as a warning.
        """
        action_subsheets = get_action_subsheets(soup)
        action_stages = soup.find_all('stage', type='Action', recursive=False)
        if action_stages:
            # Goes through all found Action stages and gets their subsheetid location
            for action_stage in action_stages:
                if action_stage.next_element.name == 'subsheetid':
                    action_stage_subsheetid = action_stage.next_element.string
                    # Find the subsheet name from the subsheetid
                    action_name = subsheetid_to_action(action_stage_subsheetid, action_subsheets)
                    error_str = "Action '{}' called in Object".format(action_stage.get('name'))
                    # Actions in the Base level are errors
                    if metadata['object type'] == Settings.OBJECT_TYPES['base']:
                        self.errors_list.append(error_as_dict(error_str, action_name))
                    else:
                        # If its a Wrapper or Surface Automation Base, ignore the Sleep Actions
                        # and flag other Actions as Warnings
                        if action_stage.resource.get('action') == 'Sleep':
                            error_str = "Sleep Action '{}' called in Object".format(action_stage.get('name'))
                            self.warning_list.append(warning_as_dict(error_str, action_name))


class CheckNoOverlyComplexActions(Consideration):
    CONSIDERATION_NAME = "Checked there are no overly complex pages that could be broken up?"
    # Settings
    PASS_HURDLE = 0
    FREQUENTLY_HURDLE = 3
    INFREQUENTLY_HURDLE = 5

    def __init__(self): super().__init__()

    def check_consideration(self, soup: BeautifulSoup, metadata):
        """Go through all stages in an Object and check that none are Action stages."""
        IGNORE_TYPES = ['SubSheetInfo', 'ProcessInfo', 'Note', 'Data', 'Collection', 'Block',
                        'Anchor', 'WaitEnd', 'Start']

        action_subsheets = get_action_subsheets(soup)
        all_stages = soup.find_all('stage', recursive=False)

        for action_id, action_name in action_subsheets:
            current_action_stages = []
            # Get all applicable stages that exist in that Action page
            for stage in all_stages:
                if stage.get('type') not in IGNORE_TYPES:
                    if stage.subsheetid and action_id == stage.subsheetid.string:
                        current_action_stages.append(stage)

            action_stages_count = len(current_action_stages)
            if action_stages_count > Settings.MAX_PAGE_STAGES:
                error_str = "Action has more than {} stages ({})".format(Settings.MAX_PAGE_STAGES, action_stages_count)
                self.errors_list.append(error_as_dict(error_str, action_name))

            elif action_stages_count > Settings.WARNING_PAGE_STAGES:
                warning_str = "Action has more than {} stages ({})" \
                    .format(Settings.WARNING_PAGE_STAGES, action_stages_count)
                self.warning_list.append(warning_as_dict(warning_str, action_name))


# Topic: Exception Handling
class CheckExceptionDetails(Consideration):
    CONSIDERATION_NAME = "Do all Exception stages have an exception detail?"
    # Settings
    PASS_HURDLE = 0
    FREQUENTLY_HURDLE = 1
    INFREQUENTLY_HURDLE = 4

    def __init__(self): super().__init__()

    def check_consideration(self, soup: BeautifulSoup, metadata):
        """Find all exception stages with empty an exception detail field."""
        logging.info("'CheckExceptionDetail method called")
        exception_stages = soup.find_all('exception')
        for exception_stage in exception_stages:
            # Exception has no detail and is not a preserve
            if not exception_stage.get('detail') and not exception_stage.get('usecurrent'):
                exception_name = exception_stage.parent.get('name')
                parent_subsheet_id = exception_stage.parent.subsheetid.string
                exception_page = soup.find('subsheet', {'subsheetid': parent_subsheet_id}).next_element.string

                self.errors_list.append(error_as_dict(exception_name, exception_page))


class CheckExceptionAppropriateTypeDetail(Consideration):
    CONSIDERATION_NAME = "Do Exceptions provide appropriate Type and Detail?"
    # Settings
    PASS_HURDLE = 0
    FREQUENTLY_HURDLE = 1
    INFREQUENTLY_HURDLE = 4
    MAX_SCORE = 5  # Almost all Objects should pass this easy check

    def __init__(self): super().__init__(self.MAX_SCORE)

    def check_consideration(self, soup: BeautifulSoup, metadata):
        """Ensure Exception details are of appropriate length and flags warnings for Business Excep in Base Objects."""
        exception_stages = soup.find_all('exception')
        action_subsheets = None

        for exception_stage in exception_stages:
            # Exception is not a preserve
            if not exception_stage.get('usecurrent'):

                if not Settings.OBJECT_TYPES['wrapper'] in metadata['object type']:
                    # If Business Exception in a Base Object
                    if 'Business' in exception_stage.get('type'):
                        if not action_subsheets:
                            action_subsheets = get_action_subsheets(soup)
                        exception_name = exception_stage.parent.get('name')
                        parent_subsheet_id = exception_stage.parent.subsheetid.string
                        exception_page_name = subsheetid_to_action(parent_subsheet_id, action_subsheets)
                        warning_str = "Business Exception in a Base Object: '{}'".format(exception_name)
                        self.warning_list.append(warning_as_dict(warning_str, exception_page_name))

                # If Exception detail length not adequate
                detail_length = len(exception_stage.get('detail'))
                # Flag an error
                if detail_length < Settings.MIN_DETAIL_LENGTH:
                    if not action_subsheets:
                        action_subsheets = get_action_subsheets(soup)
                    exception_name = exception_stage.parent.get('name')
                    exception_detail = exception_stage.get('detail')
                    parent_subsheet_id = exception_stage.parent.subsheetid.string
                    exception_page_name = subsheetid_to_action(parent_subsheet_id, action_subsheets)
                    error_str = "Exception '{}' has less than {} characters ({})\n{}" \
                        .format(exception_name, Settings.MIN_DETAIL_LENGTH, detail_length, exception_detail)
                    self.errors_list.append(error_as_dict(error_str, exception_page_name))

                # Flag a Warning
                elif detail_length < Settings.WARNING_DETAIL_LENGTH:
                    if not action_subsheets:
                        action_subsheets = get_action_subsheets(soup)
                    exception_name = exception_stage.parent.get('name')
                    exception_detail = exception_stage.get('detail')
                    parent_subsheet_id = exception_stage.parent.subsheetid.string
                    exception_page_name = subsheetid_to_action(parent_subsheet_id, action_subsheets)
                    warning_str = "Exception '{}' has less than {} characters ({})\n{}"\
                        .format(exception_name, Settings.WARNING_DETAIL_LENGTH, detail_length, exception_detail)
                    self.warning_list.append(warning_as_dict(warning_str, exception_page_name))


class CheckExceptionType(Consideration):
    CONSIDERATION_NAME = "Do Exception Types follow Best Practice?"
    # Settings
    PASS_HURDLE = 0
    FREQUENTLY_HURDLE = 1
    INFREQUENTLY_HURDLE = 3

    def __init__(self): super().__init__()

    def check_consideration(self, soup: BeautifulSoup, metadata):
        EXCEPTION_TYPE_WHITELIST = ['system exception', 'business exception']
        exception_stages = soup.find_all('exception')
        for exception_stage in exception_stages:
            # Ignore preserve exceptions
            if not exception_stage.get('usecurrent'):
                exception_name = exception_stage.parent.get('name')
                exception_type = exception_stage.get('type')

                if not exception_type:
                    parent_subsheet_id = exception_stage.parent.subsheetid.string
                    action_subsheets = get_action_subsheets(soup)
                    exception_page = subsheetid_to_action(parent_subsheet_id, action_subsheets)
                    error_str = "'{}' has no Exception Type".format(exception_name)
                    self.errors_list.append(error_as_dict(error_str, exception_page))

                else:
                    if not any(correct_type in exception_type.lower() for correct_type in EXCEPTION_TYPE_WHITELIST):
                        parent_subsheet_id = exception_stage.parent.subsheetid.string
                        action_subsheets = get_action_subsheets(soup)
                        exception_page = subsheetid_to_action(parent_subsheet_id, action_subsheets)
                        error_str = "'{}' has Exception Type of '{}'".format(exception_name, exception_type)
                        self.errors_list.append(error_as_dict(error_str, exception_page))


# Topic: Logging
class CheckLoggingAdhereToPolicy(Consideration):
    """Checks if any stages have logging turned on when Process is in production,

    Check ignores Exception stages, which it allows logging to remain on for in Production.
    This check also ignores any stages where logging is not an option that can be turned off.
    """
    CONSIDERATION_NAME = "Does logging adhere to local Security Policy?"
    # Settings
    PASS_HURDLE = 0
    FREQUENTLY_HURDLE = 3
    INFREQUENTLY_HURDLE = 6

    def __init__(self): super().__init__()

    def check_consideration(self, soup: BeautifulSoup, metadata):
        IGNORE_TYPES = ['SubSheetInfo', 'ProcessInfo', 'Note', 'Data', 'Collection', 'Block', 'Anchor']
        if metadata['additional info']['Delivery Stage'] == 'Production':
            action_subsheets = get_action_subsheets(soup)
            all_stages = soup.find_all('stage', recursive=False)

            for stage in all_stages:
                stage_name = stage.get('name')
                stage_type = stage.get('type')

                if stage_type not in IGNORE_TYPES:
                    if stage.loginhibit:
                        if stage.loginhibit.get('onsuccess'):
                            # Ready for if SAM business rules are updated
                            # print("Error Only: {} of  {}".format(stage_name, stage_type))
                            pass
                        else:
                            # print("Disabled: {} of  {}".format(stage_name, stage_type))
                            pass
                    elif stage_type != 'Exception':
                        if stage.subsheetid:
                            action_name = subsheetid_to_action(stage.subsheetid.string, action_subsheets)
                        error_str = "Logging Enabled: {} stage '{}'".format(stage_type, stage_name)
                        self.errors_list.append(error_as_dict(error_str, action_name))


# Topic: Images
class CheckImageDefinitionsEfficient(Consideration):
    """Checks if a Wait stage times out to an Exception or End stage.

    If a Wait stage times out to an Anchor stage, it will keep following the successive anchors until it reaches
    a non-anchor stage.
    """
    CONSIDERATION_NAME = "Are Target Images definitions efficient?"
    # Settings
    PASS_HURDLE = 0
    FREQUENTLY_HURDLE = 2
    INFREQUENTLY_HURDLE = 3

    def __init__(self): super().__init__()

    def check_consideration(self, soup: BeautifulSoup, metadata):
        data_stages = soup.find_all('stage', type='Data', recursive=False)
        for data_stage in data_stages:
            if data_stage.datatype.string == 'image':
                image_str = data_stage.initialvalue.string

                commas_found = 0
                width = ''
                height = ''
                # initialvalue string in form widthNum,heightNum,restOfString
                for pos, char in enumerate(image_str):
                    if commas_found == 0:
                        if not char == ",":
                            width += char
                        else:
                            commas_found += 1
                    elif commas_found == 1:
                        if not char == ",":
                            height += char
                        else:
                            break

                if int(width) > Settings.MAX_WIDTH:
                    action_subsheets = get_action_subsheets(soup)
                    action_name = subsheetid_to_action(data_stage.subsheetid.string, action_subsheets)
                    if int(height) > Settings.MAX_HEIGHT:
                        error_str = "Data Item '{}' has Height: {} and Width: {}" \
                            .format(data_stage.get('name'), height, width)
                        self.errors_list.append(error_as_dict(error_str, action_name))
                    else:
                        error_str = "Data Item '{}' has Width: {}" \
                            .format(data_stage.get('name'), width)
                        self.errors_list.append(error_as_dict(error_str, action_name))

                elif int(height) > Settings.MAX_HEIGHT:
                    action_subsheets = get_action_subsheets(soup)
                    action_name = subsheetid_to_action(data_stage.subsheetid.string, action_subsheets)
                    error_str = "Data Item '{}' has Height: {}" \
                        .format(data_stage.get('name'), height)
                    self.errors_list.append(error_as_dict(error_str, action_name))


# Topic: Application Focus
class CheckFocusUsedForGlobals(Consideration):
    CONSIDERATION_NAME = "Is Focus ensured when required? For using Globals and Image Recognition?"
    # Settings
    PASS_HURDLE = 0
    FREQUENTLY_HURDLE = 2
    INFREQUENTLY_HURDLE = 3

    def __init__(self): super().__init__()

    def check_consideration(self, soup: BeautifulSoup, metadata):
        global_nav_subsheetids = []
        global_read_subsheetids = []
        activate_app_subsheetids = []
        aafocus_subsheetids = []

        navigate_stages = soup.find_all('stage', type='Navigate', recursive=False)
        read_stages = soup.find_all('stage', type='Read', recursive=False)
        action_subsheets = get_action_subsheets(soup)

        # Check if any Navigate stages contain steps requiring application at forefront
        for navigate_stage in navigate_stages:
            stage_name = navigate_stage.get('name')
            steps = navigate_stage.find_all('step', recursive=False)
            for step in steps:
                step_name = step.action.id.string
                if step_name == 'ActivateApp':
                    subsheetid = step.parent.subsheetid.string
                    activate_app_subsheetids.append(subsheetid)

                elif any(global_nav in step_name for global_nav in Settings.GLOBAL_NAV_STEPS):
                    subsheetid = step.parent.subsheetid.string
                    global_nav_subsheetids.append(subsheetid)

                elif step_name == 'AAFocus':
                    subsheetid = step.parent.subsheetid.string
                    aafocus_subsheetids.append(subsheetid)

        # Check if any Read stages contain steps requiring application at forefront
        for read_stage in read_stages:
            steps = read_stage.find_all('step', recursive=False)
            for step in steps:
                step_name = step.action.id.string
                if any(global_read in step_name for global_read in Settings.GLOBAL_READ_STEPS):
                    subsheetid = step.parent.subsheetid.string
                    global_read_subsheetids.append(subsheetid)

        # Removes duplicate subsheetids from lists
        global_nav_subsheetids = list(dict.fromkeys(global_nav_subsheetids))
        global_read_subsheetids = list(dict.fromkeys(global_read_subsheetids))
        activate_app_subsheetids = list(dict.fromkeys(activate_app_subsheetids))
        aafocus_subsheetids = list(dict.fromkeys(aafocus_subsheetids))

        navs_with_no_activateapp = [global_nav_subsheetid for global_nav_subsheetid in global_nav_subsheetids
                                    if global_nav_subsheetid not in activate_app_subsheetids]
        reads_with_no_activateapp = [global_read_subsheetid for global_read_subsheetid in global_read_subsheetids
                                     if global_read_subsheetid not in activate_app_subsheetids]
        subsheets_using_focusaa = [subsheet_uses_focus for subsheet_uses_focus in aafocus_subsheetids
                                   if subsheet_uses_focus not in activate_app_subsheetids]

        if navs_with_no_activateapp:
            for subsheet_using_focusaa in subsheets_using_focusaa:
                # If Action has global nav, no activate app stage but has a FocusAA stage, add it to the warning list
                if subsheet_using_focusaa in navs_with_no_activateapp:
                    navs_with_no_activateapp.remove(subsheet_using_focusaa)
                    action_name = subsheetid_to_action(subsheet_using_focusaa, action_subsheets)
                    warning_str = "Global click or send key with a 'FocusAA' but no 'Activate Application' stage"
                    self.warning_list.append(warning_as_dict(warning_str, action_name))

            for nav_with_no_activate in navs_with_no_activateapp:
                action_name = subsheetid_to_action(nav_with_no_activate, action_subsheets)
                error_str = "Global click or send key in Action without an 'Activate Application' stage"
                self.errors_list.append(error_as_dict(error_str, action_name))

        if reads_with_no_activateapp:
            for read_with_no_activateapp in reads_with_no_activateapp:
                action_name = subsheetid_to_action(read_with_no_activateapp, action_subsheets)
                error_str = "Global Read stage within Action without an 'Activate Application' stage"
                self.errors_list.append(error_as_dict(error_str, action_name))
