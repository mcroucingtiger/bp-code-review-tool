from bs4 import BeautifulSoup, Tag
import logging
import inspect
import sys
import re
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
    """Check action name doesn't contain blacklisted words."""
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
# Topic: Application Modeller Tree broken down
class CheckElementsLogicallyBrokenDown(Consideration):
    """Check App Model tree has at least two levels of descendants."""
    CONSIDERATION_NAME = "Are the elements logically broken down by screen or each part of the screen?"
    #Settings
    MAX_ERROR_SCORE = 5

    def __init__(self): super().__init__(self.MAX_ERROR_SCORE)

    def check_consideration(self, soup: BeautifulSoup, metadata):
        appdef = soup.find('appdef', recursive=False)
        inherits_app_model = soup.find('parentobject', recursive=False)

        if metadata['object type'] == Settings.OBJECT_TYPES['base']:
            # Ensure the base Object has an application model
            if appdef:
                # Check the number of elements in the App Model
                elements = appdef.find_all('element')
                element_count = len(elements)
                if element_count >= Settings.MAX_ELEMENT_COUNT:
                    error_str = "Object has over {} spied elements ({}). Object size is probably too large" \
                        .format(Settings.MAX_ELEMENT_COUNT, element_count)
                    self.warning_list.append(error_as_dict(error_str, ''))
                    print(error_str)
                elif element_count >= Settings.WARNING_ELEMENT_COUNT:
                    warning_str = "Object has over {} spied elements ({}). Check if Object is adequately granular"\
                        .format(Settings.WARNING_ELEMENT_COUNT, element_count)
                    self.warning_list.append(warning_as_dict(warning_str, ''))
                    print(warning_str)

                # Check the App Model tree isn't flat
                if not inherits_app_model:
                    root_children = appdef.element.contents
                    # Iterates through root child element to ensure the tree has at least two descendants
                    for root_child in root_children:
                        if root_child.name == 'element':
                            # root - element - element
                            second_child_element = root_child.element
                            if second_child_element:
                                return
                            # root - element - group
                            second_child_group = root_child.group
                            if second_child_group:
                                return
                        elif root_child.name == 'group':
                            # root - group - group
                            second_child_group = root_child.group
                            if second_child_group:
                                return
                            # root - group - element
                            second_child_element = root_child.element
                            if second_child_element:
                                return

                    # Flat App Model found
                    if element_count < 10:
                        warning_str = "Flat App Model tree found, but tree contains less than {} elements ({})"\
                            .format(Settings.WARNING_ELEMENT_MINIMUM, element_count)
                        self.warning_list.append(warning_as_dict(warning_str, ""))
                        print(warning_str)
                    else:
                        error_str = "Application Model tree has less than two child descendants (not organised by page)"
                        self.errors_list.append(error_as_dict(error_str, ""))
                        print(error_str)
            else:
                error_str = "Base Object that does not have an App Model nor inherit one."
                self.errors_list.append(error_as_dict(error_str, ""))
                print(error_str)

        elif metadata['object type'] == Settings.OBJECT_TYPES['surface auto base']:
            # Ensure the base Object has an application model
            if appdef:
                if not inherits_app_model:
                    # Check the App Modeller contains region container elements
                    region_container = appdef.find('region-container')
                    if not region_container:
                        error_str = "Surface Automation base Object doesn't have any region elements"
                        self.errors_list.append(error_as_dict(error_str, ""))

        # Object is a wrapper and so has no App Model to check (though not always the case)
        else:
            self._force_result(Result.NOT_APPLICABLE, 0, 0)


# Topic: Element - Names
class CheckElementNamesFollowBestPractice(Consideration):
    # TODO: Ensure the metadata from checklist contains a check to flip the order name/type. This is used
    #  in the method params of _check_element_title

    CONSIDERATION_NAME = "Do the element names follow BP best practice or local naming convention?"

    APPLICATION_TYPES = ['HTML', 'Java', 'Win32', 'Browser', 'Mainframe']
    ELEMENT_TYPE_WHITELIST = ['box', 'button', 'label', 'field', 'link', 'text', 'tab', 'main', 'title', 'window',
                              'region', 'list', 'popup', 'input', 'header', 'section', 'table', 'element',
                              'edit', 'toolbar']
    # Settings
    PASS_HURDLE = 0
    FREQUENTLY_HURDLE = 3
    INFREQUENTLY_HURDLE = 5

    def __init__(self): super().__init__()

    def check_consideration(self, soup: BeautifulSoup, metadata):
        """Check that best practice was used when naming the App Modeller tree elements."""
        if metadata['object type'] != Settings.OBJECT_TYPES['wrapper']:
            appdef = soup.find('appdef', recursive=False)
            inherits_app_model = soup.find('parentobject', recursive=False)
            elements = appdef.find_all('element')

            if appdef:  # Ensure the base Object has an application model
                if not inherits_app_model:
                    application_type = appdef.apptypeinfo.id.string.replace('Launch', '').replace('Attach', '')
                    if application_type not in self.APPLICATION_TYPES:
                        error_str = "Unknown application type"
                        self.errors_list.append(error_as_dict(error_str, application_type))
                        self._force_result(Result.NO, 0)  # Can't evaluate if don't recognise application type

                    root_element_found = False
                    for element in elements:
                        if not root_element_found:
                            element_basetype = element.find('basetype', recursive=False).string
                            if element_basetype == 'Application':
                                root_element_found = True
                            if root_element_found:  # Skip the root element
                                continue
                        self._check_element_title(element, application_type)

                    # Checks specific to Surface Automation Base Objects
                    if metadata['object type'] == Settings.OBJECT_TYPES['surface auto base']:
                        regions = appdef.find_all('region')
                        for region in regions:
                            region_name = region.get('name')
                            if self._element_is_dynamic(region):
                                if 'dynamic' not in region_name.lower():
                                    warning_str = "Region has a dynamic attribute. " \
                                                  "Please include 'Dynamic' in the element name"
                                    self.warning_list.append(warning_as_dict(warning_str, region_name))

                # Object doesn't have it's own App Model to search (inherits)
                else:
                    self._force_result(Result.NOT_APPLICABLE, 0, 0)
            else:
                error_str = "Base Object that does not have an App Model nor does it inherit one."
                self.errors_list.append(error_as_dict(error_str, ""))

        else:
            self._force_result(Result.NOT_APPLICABLE, 0, 0)

    def _check_element_title(self, element: Tag, application_type: str, element_type_start=True):
        """Check the element name conforms to best practice and add a warning/error if it does not.

        Best practice is to have the element type, hyphen, element name and then if necessary (dynamic) if it uses any
        dynamic attributes and the spy mode if it is not the elements native spy mode in brackets on the end
        e.g. 'Field - Username (Dynamic) (Win32)'

         Args:
             element: The element tag to be checked.
             application_type: How the App Modeller has been set to recognise the application (Win32, Java, Browser)
             element_type_start: Local naming convention order for which side of the hyphen type/name goes.
                False for "element_name - element_type"

        Returns:
            bool: If the element conforms to best practice.  True for success, False otherwise.

         """

        WIN32_ELEMENT_TYPES = ['window', 'radio button', 'check box', 'button', 'edit', 'list box', 'combo box',
                               'tree view', 'tab control', 'track bar', 'up-down box', 'datetime picker',
                               'month calendar picker', 'scroll bar', 'label', 'toolbar', '.net datagrid',
                               '.net datagridview']

        element_name = element.get('name')
        element_base_type = element.find('basetype', recursive=False).string
        type_idx, name_idx = 0, 1

        if not element_type_start:
            type_idx, name_idx = 1, 0

        # Check correct use of hyphen for formatting
        element_list = element_name.split(' - ')
        if not self._correct_hyphen_formatting(element_name, element_list):
            return False

        # Check the element type within the name matches the whitelist
        if any(element_type in element_list[type_idx].lower() for element_type in self.ELEMENT_TYPE_WHITELIST):
            if len(element_list[type_idx]) >= Settings.WARNING_ELEMENT_TYPE_LENGTH:
                warning_str = "Element type may be excessively long".format()
                self.warning_list.append(warning_as_dict(warning_str, element_list[type_idx]))
        # If element type isn't valid, flag error and strip spy mode from element type if needed
        else:
            if not element_type_start:
                left_bracket_idx = str.rfind(element_list[1], '(')
                if left_bracket_idx != -1:
                    element_list[1] = element_list[1][0:left_bracket_idx]
            error_str = "'{}' not in the element type whitelist".format(element_list[type_idx])
            self.errors_list.append(error_as_dict(error_str, element_name))
            return False

        # Check the element type is correctly labeled, if it isn't the native app spying mode
        if application_type not in element_base_type:
            # If application is Win32, SAP spy mode doesn't need to be mentioned in brackets
            if 'SAP' in element_base_type and application_type == 'Win32':
                pass
            # Element was spied with a mode different to the native app mode
            else:
                left_bracket_idx = str.rfind(element_list[1], '(')  # reverse find used to find the final ()
                right_bracket_idx = str.rfind(element_list[1], ')')

                # Converts Windows elements with base_type 'Button' or 'Edit' to instead be 'Win32' for consistency
                if element_base_type.lower() in WIN32_ELEMENT_TYPES:
                    element_base_type = 'Win32'

                # Check if the correct spy mode was noted in the brackets e.g. (AA)
                if left_bracket_idx != -1 and right_bracket_idx != -1:
                    given_spy_type = element_list[1][left_bracket_idx + 1:right_bracket_idx]
                    if given_spy_type.lower() != 'dynamic':
                        if given_spy_type not in element_base_type:
                            warning_str = "Stated spying mode '{}' is not the element's spy mode: '{}'" \
                                .format(given_spy_type, element_base_type)
                            self.warning_list.append(warning_as_dict(warning_str, element_name))

                    # Brackets contain 'dynamic' but Spy mode not in the brackets when it should be
                    else:
                        if application_type not in element_base_type:
                            warning_str = "Object's application type is '{}' but element's base type is '{}'. " \
                                          "Please note the spy mode within brackets at the end of the element's name" \
                                .format(application_type, element_base_type)
                            self.warning_list.append(warning_as_dict(warning_str, element_name))

                # Otherwise Spy mode not in the brackets when it should be
                else:
                    if application_type not in element_base_type:
                        warning_str = "Object's application type is '{}' but element's base type is '{}'. " \
                                      "Please note the spy mode within brackets at the end of the element's name"\
                            .format(application_type, element_base_type)
                        self.warning_list.append(warning_as_dict(warning_str, element_name))

        if self._element_is_dynamic(element):
            if 'dynamic' not in element_name.lower():
                warning_str = "Element has a dynamic attribute. Please include 'Dynamic' in the element name"
                self.warning_list.append(warning_as_dict(warning_str, element_name))

        return True

    def _correct_hyphen_formatting(self, element_name, element_list):
        """Ensure the element name contains a single hyphen for formatting purposes."""
        if len(element_list) >= 3:
            error_str = "Element name contains multiple hyphen. Use the native tree structure" \
                        " to order the app model"
            self.errors_list.append(error_as_dict(error_str, element_name))
            return False
        elif len(element_list) == 1:
            if '-' in element_name:
                error_str = "Element name contains a hyphen, but it is not properly used for formatting. " \
                            "Ensure there is a space on each side of the hyphen."
                self.errors_list.append(error_as_dict(error_str, element_name))
                False
            else:
                error_str = "Element name does not contain a hyphen to split the name for correct formatting"
                self.errors_list.append(error_as_dict(error_str, element_name))
                return False

        elif len(element_list) == 2:
            return True

    @staticmethod
    def _element_is_dynamic(element: Tag):
        attributes = element.attributes
        if attributes.find('attribute', comparisontype='dynamic', recursive=False) is not None:
            return True
        else:
            return False


# Topic: Documentation
class CheckActionsDocumentation(Consideration):
    """Pre/Post conditions are only required for Base Objects.

    If either is not found in a Wrapper, it is flagged as a Warning.
    """
    CONSIDERATION_NAME = "Are Action descriptions, Pre-Conditions, Post Conditions, Input params & " \
                         "Output params documented to create a meaningful BOD?"
    # Settings
    PASS_HURDLE = 0
    FREQUENTLY_HURDLE = 3
    INFREQUENTLY_HURDLE = 6
    MAX_SCORE = 5

    def __init__(self): super().__init__(self.MAX_SCORE)

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
                    self.errors_list.append(error_as_dict("Missing Action Description", action_name))

        # Find input and output param descriptions
        for start_stage in start_stages:
            if start_stage.inputs:
                for input_param in start_stage.inputs.contents:
                    if isinstance(input_param, Tag):
                        if not input_param.get('narrative'):
                            param_name = input_param.get('name')
                            start_stage_id = start_stage.subsheetid.string
                            action_name = subsheetid_to_action(start_stage_id, action_subsheets)
                            error_str = "Missing input param description: {}".format(param_name)
                            self.errors_list.append(error_as_dict(error_str, action_name))

        for end_stage in end_stages:
            if end_stage.outputs:
                for output_param in end_stage.outputs.contents:
                    if isinstance(output_param, Tag):
                        if not output_param.get('narrative'):
                            param_name = output_param.get('name')
                            end_stage_id = end_stage.subsheetid.string
                            action_name = subsheetid_to_action(end_stage_id, action_subsheets)
                            error_str = "Missing output param description: {}".format(param_name)
                            self.errors_list.append(error_as_dict(error_str, action_name))

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
                        # If the Object is a Wrapper, flag a warning. If it's a Base Object, flag as an error.
                        # Base Surface Automation Objects don't require a pre/post condition due to their nature.
                        if metadata['object type'] == Settings.OBJECT_TYPES['wrapper']:
                            error_str += ' in Wrapper'
                            self.warning_list.append(warning_as_dict(error_str, action_name))
                        elif metadata['object type'] == Settings.OBJECT_TYPES['base']:
                            self.errors_list.append(error_as_dict(error_str, action_name))


# Topic: Exposure
class CheckObjectExposureValid(Consideration):
    """Check the current Object exposure is valid.

    Checks to see if an application model exists. If one does, then checks the Object's exposure type. If it is using
    an application model, then the Object must be interacting with the UI. Therefore the exposure should not be set
    to Background
    """
    CONSIDERATION_NAME = "Are the Business Object exposures valid?"

    # Settings
    MAX_SCORE = 4

    def __init__(self): super().__init__(self.MAX_SCORE)

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

        # Consideration not applicable to wrappers
        else:
            self._force_result(Result.NOT_APPLICABLE, 0, 0)


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

        # Wrapper Actions do not require an Attach as the first stage.
        # Check the Action does not contain a word from the blacklist and ensure the first stage is a Attach.
        if metadata['object type'] != Settings.OBJECT_TYPES['wrapper']:
            for action_page in action_pages:
                action_name = action_page.next_element.string
                if action_not_blacklisted(BLACKLIST_ACTION_NAMES, action_name):
                    if not self._action_begins_attach(action_page, start_stages, page_reference_stages):
                        error_str = "Action doesn't start with Attach stage"
                        self.errors_list.append(error_as_dict(error_str, action_name))

        # Consideration not applicable to wrappers
        else:
            self._force_result(Result.NOT_APPLICABLE, 0, 0)

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
    CONSIDERATION_NAME = "Does each Action start with a Wait Stage to verify " \
                         "the application is in the correct state?"
    # Settings
    PASS_HURDLE = 0
    FREQUENTLY_HURDLE = 1
    INFREQUENTLY_HURDLE = 4

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
                                                if 'exists' in choice.lower() or 'loaded' in choice.lower():
                                                    check_exists = True
                                                    break
                                            if not check_exists:
                                                error_str = "Wait stage following Attach, but no 'Check Exists'"
                                                self.errors_list.append(error_as_dict(error_str, action_name))
                                        else:
                                            error_str = "Wait stage following Attach has no conditions"
                                            self.errors_list.append(error_as_dict(error_str, action_name))
                                    else:
                                        error_str = "Attach page not followed by a Wait stage"
                                        self.errors_list.append(error_as_dict(error_str, action_name))
                                else:
                                    error_str = 'Action doesnt start with Attach'
                                    self.errors_list.append(error_as_dict(error_str, action_name))

        # Consideration not applicable to wrappers
        else:
            self._force_result(Result.NOT_APPLICABLE, 0, 0)


class CheckGlobalTimeoutUsedWaits(Consideration):
    """Checks that Global timeout data items exist on the Initialise page and ensure that they are used for
    all Wait stages within the Object.

    Scoring is based on amount of errors, and as it can't distinguish between the error of having no global data items
    vs not using global data items in a couple Wait stages, any error will result in a hrad fail.
    """
    CONSIDERATION_NAME = "Global variable enable a quick change to timeout values when application " \
                         "behaviour dictates."

    # Settings
    PASS_HURDLE = 0
    FREQUENTLY_HURDLE = 1
    INFREQUENTLY_HURDLE = 4
    MAX_SCORE = 5

    def __init__(self): super().__init__(self.MAX_SCORE)

    def check_consideration(self, soup: BeautifulSoup, metadata):
        # Don't check wait stages if Surface Automation used
        # TODO: Need a better implementation of this. Makes this completely redundant for surface automation
        if metadata['additional info']['Surface Automation Used?'] == 'TRUE':
            self._force_result(Result.NOT_APPLICABLE, 0, 0)
            return

        data_stages = soup.find_all('stage', type='Data')
        wait_stages = soup.find_all('stage', type='WaitStart')

        init_data_items = []
        for data_stage in data_stages:
            if data_stage.subsheetid is None:  # Any stages on the init page have no subsheetid
                init_data_items.append(data_stage.get('name'))

        if not init_data_items:
            self.errors_list.append(error_as_dict("No global timeout Data items", "Initialise"))
            self._force_result(Result.NO, 0)
            return

        for wait_stage in wait_stages:
            timeout = wait_stage.timeout.string
            if not any(init_data_item in timeout for init_data_item in init_data_items):
                action_subsheets = get_action_subsheets(soup)
                action_name = subsheetid_to_action(wait_stage.subsheetid.string, action_subsheets)
                wait_stage_name = wait_stage.get('name')
                error_string = "Wait stage '{}' has timeout value: {}".format(wait_stage_name, timeout, action_name)
                self.errors_list.append(error_as_dict(error_string, action_name))


class CheckWaitNotArbitrary(Consideration):
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
            self._force_result(Result.NOT_APPLICABLE, 0, 0)
            return

        if metadata['object type'] != Settings.OBJECT_TYPES['wrapper']:
            action_subsheets = None
            wait_stages = soup.find_all('stage', type='WaitStart', recursive=False)
            if wait_stages:
                for wait_stage in wait_stages:
                    if len(wait_stage.choices) == 0:
                        if not action_subsheets:
                            action_subsheets = get_action_subsheets(soup)
                        action_name = subsheetid_to_action(wait_stage.subsheetid.string, action_subsheets)
                        error_str = "Wait stage has no condition: '{}'".format(wait_stage.get('name'))
                        self.errors_list.append(error_as_dict(error_str, action_name))

            # Consideration not applicable if no wait stages
            else:
                self._force_result(Result.NOT_APPLICABLE, 0, 0)

        # Consideration not applicable to wrappers
        else:
            self._force_result(Result.NOT_APPLICABLE, 0, 0)


class CheckNavigateFollowedByWait(Consideration):
    CONSIDERATION_NAME = "Are navigation stages between application screens followed by a Wait stage to verify success?"
    # Settings
    PASS_HURDLE = 0
    FREQUENTLY_HURDLE = 3
    INFREQUENTLY_HURDLE = 6

    ACTION_BLACKLIST = ['attach', 'detach', 'terminate', 'close']
    ELEMENT_BASETYPE_WHITELIST = ['HTMLCombo', 'HTMLRadioButton']  # TODO: This is just HTML, need to do other modes

    def __init__(self): super().__init__()

    def check_consideration(self, soup: BeautifulSoup, metadata):
        """Check all navigate stages to ensure they are followed by a Wait or End stage.

        If the Navigate uses a 'Pause between each step' value, this will be accepted as a wait. This check will also
        try to determine if the navigate is selecting an item on the screen (e.g. a check box) that does not require a
        Wait after. This feature may be unnecessary.

        This check is only applicable to normal base Objects.
        """
        if metadata['object type'] == Settings.OBJECT_TYPES['base']:
            action_subsheets = None
            navigate_stages = soup.find_all('stage', type='Navigate', recursive=False)

            if navigate_stages:
                if not action_subsheets:
                    action_subsheets = get_action_subsheets(soup)
                for navigate_stage in navigate_stages:
                    if navigate_stage.onsuccess is not None:
                        action_name = subsheetid_to_action(navigate_stage.subsheetid.string, action_subsheets)
                        if action_not_blacklisted(self.ACTION_BLACKLIST, action_name):
                            current_stage = navigate_stage
                            # Keep going through success stages while they are Anchors
                            while True:
                                success_stage = soup.find('stage', stageid=current_stage.onsuccess.string,
                                                          recursive=False)
                                success_type = success_stage.get('type')
                                if not success_type == 'Anchor':
                                    break
                                else:
                                    current_stage = success_stage

                            # Check if the next stage isn't a Wait or an End
                            if success_type != 'WaitStart' and success_type != 'End':
                                # Accept a 'Pause after each step' as a Wait
                                if navigate_stage.get('interval') is None:
                                    self._check_element_is_selectable(navigate_stage, action_name, soup)
                    else:
                        action_name = subsheetid_to_action(navigate_stage.subsheetid.string, action_subsheets)
                        error_str = "Navigate stage isn't connected to another stage"
                        self.errors_list.append(error_as_dict(error_str, action_name))
            # Consideration not applicable if no navigate stages
            else:
                self._force_result(Result.NOT_APPLICABLE, 0, 0)
        # Consideration not applicable to wrappers or Surface Auto bases
        else:
            self._force_result(Result.NOT_APPLICABLE, 0, 0)

    def _check_element_is_selectable(self, navigate_stage, action_name, soup):
        """Check each step in a Navigate stage to see if any application elements are selectable."""
        navigate_steps = navigate_stage.find_all('step', recursive=False)
        error_str, warning_str = '', ''

        for navigate_step in navigate_steps:
            # Find the element being used by the Navigate so that it can be determined if  combo box is being selected
            element_id = navigate_step.element.get('id')
            if element_id:
                element = soup.find('id', text=element_id)
                if element:  # element wont be found if App Model is inherited
                    element_datatype = element.parent.datatype.string
                    element_basetype = element.parent.basetype
                    # Navigate is changing value of flag, so is acceptable without Wait
                    if element_datatype == 'flag':
                        return
                    elif any(basetype in element_basetype for basetype in self.ELEMENT_BASETYPE_WHITELIST):
                        # print("PASS basetype: '{}', datatype '{}'".format(element_basetype, element_datatype))
                        return
                    else:
                        # print("FAIL basetype: '{}', datatype '{}'".format(element_basetype, element_datatype))
                        error_str = "Navigate stage not followed by a Wait stage: '{}'" \
                            .format(navigate_stage.get('name'))
                else:
                    warning_str = "Navigate '{}' not followed by a Wait or End, but App Model is inherited " \
                                  "so can't determine if a Wait is necessary".format(navigate_stage.get('name'))
                    self.warning_list.append(warning_as_dict(warning_str, action_name))
                    return

        # If no stages in the Navigate are selecting a combo box, Navigate added to error list
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
        if metadata['object type'] != Settings.OBJECT_TYPES['wrapper']:
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

        # Consideration not applicable to wrappers
        else:
            self._force_result(Result.NOT_APPLICABLE, 0, 0)


# Topic: Re-useable Actions
class CheckObjectsNoBusinessLogic(Consideration):
    CONSIDERATION_NAME = "Is there no Business Logic that should be in a Process?"
    # Settings
    PASS_HURDLE = 0
    FREQUENTLY_HURDLE = 4
    INFREQUENTLY_HURDLE = 7
    # TODO: Wait for response from Xave about checking Base objects

    def __init__(self): super().__init__()

    def check_consideration(self, soup: BeautifulSoup, metadata):
        decision_stages = soup.find_all('stage', type='Decision', recursive=False)
        choice_stages = soup.find_all('stage', type='ChoiceStart', recursive=False)
        action_subsheets = None
        LOOP_COUNTER_WHITELIST = ['retry', 'retries', 'loop', 'count']
        BASE_ACTION_DECISION_WHITELIST = ['attach', 'detach', 'launch', 'terminate']

        # Ensure there are no choice or decision stages in base Objects,
        # except for Attach and Detach Actions
        if metadata['object type'] == Settings.OBJECT_TYPES['base']:
            if choice_stages:
                for choice_stage in choice_stages:
                    if not action_subsheets:
                        action_subsheets = get_action_subsheets(soup)
                    subsheetid = choice_stage.subsheetid.string
                    action_name = subsheetid_to_action(subsheetid, action_subsheets)
                    stage_name = choice_stage.get('name')
                    error_str = "Choice stage '{}' in a base Object".format(stage_name)
                    self.errors_list.append(error_as_dict(error_str, action_name))
                    print(error_str)
                    print(action_name)

            if decision_stages:
                for decision_stage in decision_stages:
                    if not action_subsheets:
                        action_subsheets = get_action_subsheets(soup)
                    subsheetid = decision_stage.subsheetid.string
                    action_name = subsheetid_to_action(subsheetid, action_subsheets)
                    if not any(whitelist_action in action_name.lower()
                               for whitelist_action in BASE_ACTION_DECISION_WHITELIST):
                        stage_name = decision_stage.get('name')
                        expression = decision_stage.decision.get('expression')
                        error_str = "Decision stage '{}' in a base Object\nExpression: '{}'"\
                            .format(stage_name, expression)
                        self.errors_list.append(error_as_dict(error_str, action_name))
                        print(error_str)
                        print(action_name)

        # For wrapper Objects and Surface Automation Base Objects
        # ensure that any decision/choice stages are numerical comparisons or checking flags
        # Otherwise, may indicate business logic
        elif metadata['object type'] != Settings.OBJECT_TYPES['base']:
            if choice_stages:
                if not action_subsheets:
                    action_subsheets = get_action_subsheets(soup)
                for choice_stage in choice_stages:
                    choices = choice_stage.choices
                    # Checks all the choices in Multi-Choice stage to see if all of them use flags.
                    for choice in choices:
                        expression = choice.get('expression')
                        stage_name = choice_stage.get('name')
                        subsheetid = choice_stage.subsheetid.string
                        action_name = subsheetid_to_action(subsheetid, action_subsheets)
                        if not self._expression_uses_flag(expression):
                            if not self.expression_compares_with_flag(expression, soup):
                                warning_str = "\nChoice stage '{}' has decision not based on a flag Data item. " \
                                              "This could suggest Process logic in a Business Object." \
                                              "\nExpression '{}"\
                                    .format(stage_name, expression)
                                self.warning_list.append(warning_as_dict(warning_str, action_name))
                                print(warning_str)
                                print(action_name)  # TODO: Get rid of the \n in the name
                                break

            if decision_stages:
                if not action_subsheets:
                    action_subsheets = get_action_subsheets(soup)
                for decision_stage in decision_stages:
                    decision_name = decision_stage.get('name').lower()
                    # Decision name doesn't demonstrate that it is a loop
                    if not any(loop_string in decision_name for loop_string in LOOP_COUNTER_WHITELIST):
                        expression = decision_stage.decision.get('expression')
                        stage_name = decision_stage.get('name')
                        subsheetid = decision_stage.subsheetid.string
                        action_name = subsheetid_to_action(subsheetid, action_subsheets)
                        if not self._expression_uses_flag(expression):
                            if not self.expression_compares_with_flag(expression, soup):
                                warning_str = "\nDecision could potentially indicate Business logic " \
                                              "appropriate for the Process level. \nDecision name: '{}' \nExpression: '{}'"\
                                    .format(stage_name, expression)
                                self.warning_list.append(warning_as_dict(warning_str, action_name))
                                print(warning_str)
                                print("Action name: " + action_name)

    @staticmethod
    def _expression_uses_flag(expression):
        """Check decision's expression is based on a flag data item.

        Decisions to check flags can be of the form 'flag_data_item = True' or 'flag_data_item'.
        Checks for 'foo = True' or '[foo]' as flag expressions.

        Args:
            expression (str): The decision's expression.

        Returns:
            bool: True for success, False otherwise.

        """
        COMPARISON_SIGNS = ['=', '<>', '>', '>=', '<', '<=']
        # Checks for 'foo = True', if not then checks for '[foo]'
        if 'True' in expression or 'False' in expression:
            return True
        elif any(comparison in expression for comparison in COMPARISON_SIGNS):
            return False
        else:
            return True

    @staticmethod
    def expression_compares_with_flag(expression, soup: BeautifulSoup):
        """Check if the expression is a comparison of two Data items of type Flag."""
        # Removes all text within the brackets
        removed_dataitems = re.sub('\[.*?\]', '[]', expression).replace(' ', '')
        if removed_dataitems == '[]=[]' or removed_dataitems == '[]<>[]':
            # Extract last Data item in expression to check if its a flag
            data_item_name = expression[expression.rfind("[") + 1:expression.rfind("]")]
            data_item = soup.find('stage', {'name': data_item_name}, type='Data', recursive=False)
            if data_item:
                if data_item.datatype.string == 'flag':
                    return True
        return False

    def evaluate_score_and_result(self, forced_score_scale=None, forced_result=None):
        """Calculate or set the consideration's score and result.

        Overridden so that it counts the number or warnings instead of errors.
        If no forced values are given, the default if any error exists is a hard fail {score: 0, result: No}.
        """
        # Both forced results are given from config
        if forced_score_scale and forced_result:
            self.score = self.max_score * forced_score_scale
            self.result = forced_result

        # If no forced result is given from the Config file
        # and no forced result is given from within the Consideration check
        else:
            if not self.result_forced:
                if self.warning_list or self.errors_list:
                    # Calculate score on which ever list is larger,
                    # but don't calculate on warnings if less than 3 warnings
                    errors_amount = len(self.errors_list)
                    warnings_amount = len(self.warning_list)
                    if errors_amount >= warnings_amount or warnings_amount <= 3:
                        issues_amount = errors_amount
                    else:
                        issues_amount = warnings_amount

                    if issues_amount > self.INFREQUENTLY_HURDLE:
                        self.score = 0
                        self.result = Result.NO

                    elif self.FREQUENTLY_HURDLE < issues_amount <= self.INFREQUENTLY_HURDLE:
                        self.score = self.max_score * self.INFREQUENTLY_SCALE
                        self.result = Result.INFREQUENTLY

                    elif self.PASS_HURDLE < issues_amount <= self.FREQUENTLY_HURDLE:
                        self.score = self.max_score * self.FREQUENTLY_SCALE
                        self.result = Result.FREQUENTLY

                    elif issues_amount <= self.PASS_HURDLE:
                        self.score = self.max_score
                        self.result = Result.YES

                # No Warnings
                else:
                    self.score = self.max_score
                    self.result = Result.YES


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

        # Consideration not applicable to wrappers
        if ['object type'] == Settings.OBJECT_TYPES['wrapper']:
            self._force_result(Result.NOT_APPLICABLE, 0, 0)

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
                        # If its a Wrapper or Surface Automation Base, consideration is not applicable
                        # and flag any Sleep actions as warnings
                        self._force_result(Result.NOT_APPLICABLE, 0, 0)
                        if action_stage.resource.get('action') == 'Sleep':
                            error_str = "Sleep Action '{}' called in Object".format(action_stage.get('name'))
                            self.warning_list.append(warning_as_dict(error_str, action_name))


class CheckNoOverlyComplexActions(Consideration):
    CONSIDERATION_NAME = "Checked there are no overly complex pages that could be broken up?"
    # Settings
    PASS_HURDLE = 0
    FREQUENTLY_HURDLE = 2
    INFREQUENTLY_HURDLE = 4

    def __init__(self): super().__init__()

    def check_consideration(self, soup: BeautifulSoup, metadata):
        """Check that amount of stages per page does not exceed the limits."""
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
            if action_stages_count > Settings.MAX_STAGES_PER_PAGE:
                error_str = "Action has more than {} stages ({})"\
                    .format(Settings.MAX_STAGES_PER_PAGE, action_stages_count)
                self.errors_list.append(error_as_dict(error_str, action_name))

            elif action_stages_count > Settings.WARNING_STAGES_PER_PAGE:
                warning_str = "Action has more than {} stages ({})" \
                    .format(Settings.WARNING_STAGES_PER_PAGE, action_stages_count)
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
                if metadata['object type'] != Settings.OBJECT_TYPES['wrapper']:
                    # If Business Exception in a Base Object, mark as an error
                    if 'Business' in exception_stage.get('type'):
                        if not action_subsheets:
                            action_subsheets = get_action_subsheets(soup)
                        exception_name = exception_stage.parent.get('name')
                        parent_subsheet_id = exception_stage.parent.subsheetid.string
                        exception_page_name = subsheetid_to_action(parent_subsheet_id, action_subsheets)
                        error_str = "Business Exception in a Base Object: '{}'".format(exception_name)
                        self.errors_list.append(error_as_dict(error_str, exception_page_name))

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
                    error_str = "Exception '{}' has less than {} characters ({}) - {}" \
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
                    warning_str = "Exception '{}' has less than {} characters ({}) - {}"\
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
        """Check Exception type is either System or Business exception."""
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


class CheckObjectsNotRecoverExceptions(Consideration):
    CONSIDERATION_NAME = "Objects do not try to recover exceptions (should be Process logic)?"
    # Settings
    PASS_HURDLE = 0
    FREQUENTLY_HURDLE = 1
    INFREQUENTLY_HURDLE = 2

    def __init__(self): super().__init__()

    def check_consideration(self, soup: BeautifulSoup, metadata):
        ACTIONS_WHITELIST = ['attach', 'detach']
        recover_stages = soup.find_all('stage', type='Recover', recursive=False)
        action_subsheets = None
        errored_subsheetids = []  # Ensure same error doesn't appear multiple times for a single Action

        for recover_stage in recover_stages:
            # Flag a warning for Recovers in wrappers
            if metadata['object type'] == Settings.OBJECT_TYPES['wrapper']:
                if not action_subsheets:
                    action_subsheets = get_action_subsheets(soup)
                action_subsheetid = recover_stage.subsheetid.string
                if action_subsheetid not in errored_subsheetids:
                    errored_subsheetids.append(action_subsheetid)
                    action_name = subsheetid_to_action(recover_stage.subsheetid.string, action_subsheets)
                    warning_str = "Exception handling (Recover stage) in a wrapper Object"
                    self.warning_list.append(warning_as_dict(warning_str, action_name))

            # Flag errors for Recovers in base Objects
            else:
                if not action_subsheets:
                    action_subsheets = get_action_subsheets(soup)
                action_subsheetid = recover_stage.subsheetid.string
                if action_subsheetid not in errored_subsheetids:
                    errored_subsheetids.append(action_subsheetid)
                    action_name = subsheetid_to_action(recover_stage.subsheetid.string, action_subsheets)
                    # Attach and Detach actions are allowed to have some basic exceptions handling
                    if not any(whitelist_word in action_name.lower() for whitelist_word in ACTIONS_WHITELIST):
                        error_str = "Exception handling (Recover stage) in base Object"
                        self.errors_list.append(error_as_dict(error_str, action_name))

        if metadata['object type'] == Settings.OBJECT_TYPES['wrapper']:
            # Consideration scoring not applicable to wrappers
            self._force_result(Result.NOT_APPLICABLE, 0, 0)


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
        NO_LOGGING_TYPES = ['SubSheetInfo', 'ProcessInfo', 'Note', 'Data', 'Collection', 'Block', 'Anchor']

        all_disabled = True
        all_errors = True
        exception_stage_types = []
        if metadata['additional info']['Delivery Stage'] == 'Production':

            action_subsheets = get_action_subsheets(soup)
            all_stages = soup.find_all('stage', recursive=False)

            for stage in all_stages:
                stage_name = stage.get('name')
                stage_type = stage.get('type')

                if stage_type not in NO_LOGGING_TYPES:
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

        # Consideration not applicable when in Dev or Testing
        else:
            self._force_result(Result.NOT_APPLICABLE, 0, 0)


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
        action_subsheets = None
        image_found = False
        for data_stage in data_stages:
            if data_stage.datatype.string == 'image':
                image_str = data_stage.initialvalue.string
                if image_str:
                    image_found = True
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

                    # Flag error for image being too big
                    if int(width) > Settings.MAX_IMAGE_WIDTH or int(height) > Settings.MAX_IMAGE_HEIGHT:
                        if not action_subsheets:
                            action_subsheets = get_action_subsheets(soup)
                        action_name = subsheetid_to_action(data_stage.subsheetid.string, action_subsheets)
                        error_str = "Data Item '{}' larger than recommended {} x {} ({} x {})"\
                            .format(data_stage.get('name'), Settings.MAX_IMAGE_WIDTH, Settings.MAX_IMAGE_HEIGHT,
                                    height, width)
                        self.errors_list.append(error_as_dict(error_str, action_name))

                    # Flag warning for image being too big
                    if int(width) > Settings.WARNING_IMAGE_WIDTH or int(height) > Settings.WARNING_IMAGE_HEIGHT:
                        if not action_subsheets:
                            action_subsheets = get_action_subsheets(soup)
                        action_name = subsheetid_to_action(data_stage.subsheetid.string, action_subsheets)
                        warning_str = "Data Item '{}' size above warning threshold {} x {} ({} x {})" \
                            .format(data_stage.get('name'), Settings.WARNING_IMAGE_WIDTH, Settings.WARNING_IMAGE_HEIGHT,
                                    height, width)
                        self.errors_list.append(error_as_dict(warning_str, action_name))

        if not image_found:
            self._force_result(Result.NOT_APPLICABLE, 0, 0)


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
        global_stage_found = False

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
                    global_stage_found = True
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
                    global_stage_found = True
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

        if not global_stage_found:
            self._force_result(Result.NOT_APPLICABLE, 0, 0)
