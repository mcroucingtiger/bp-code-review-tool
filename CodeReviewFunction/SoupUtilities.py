"""
This module contains all functions that break down the main soup into sub-soups, and extracting basic information
out of individual soup objects.

"""

import pickle
import time
from multiprocessing import Pool
from bs4 import BeautifulSoup, SoupStrainer
from . import Settings
from collections import namedtuple
Sub_Soup = namedtuple('Sub_Soup', 'processes, objects, queues, metadata')


def extract_pickled_soups(xml_string) -> namedtuple:
    """Turn the xml into a list of pickled soups containing processes, objects, queues and the metadata.

    :param xml_string: The full xml from the HTTP request.
    :return: Sub_Soup object containing a individual soup for each section of the BP release.
    """

    print("Extracting without multi-processing xml")
    start = time.clock()
    results = []
    strainers = ['process', 'object', 'work-queue', 'header']
    for strainer in strainers:
        results.append(_extract_soup_from_xml(strainer, xml_string))
    end = time.clock()
    print('Time to extract without multi-processing all xmls: ' + str(end - start))

    return Sub_Soup(results[0], results[1], results[2], results[3])


def _extract_soup_from_xml(strainer_param, xml_string):
    """Create a single soup object from the full xml_string and return it in str form."""
    if strainer_param == 'header':
        soup_strainer = SoupStrainer(strainer_param)
        individual_soup = BeautifulSoup(xml_string, 'lxml', parse_only=soup_strainer)

    elif strainer_param == 'process' or strainer_param == 'work-queue':
        soup_strainer = SoupStrainer(strainer_param, xmlns=True)
        individual_soup = BeautifulSoup(xml_string, 'lxml', parse_only=soup_strainer)

    elif strainer_param == 'object':
        soup_strainer = SoupStrainer('process', {"type": "object"})
        individual_soup = BeautifulSoup(xml_string, 'lxml', parse_only=soup_strainer)

    return individual_soup


# TODO: These two below should probably be in CodeReview
def dump_pickled_results(results):
    """Pickle the results list and save to a file to skip this step when testing"""
    file_location = "C:/Users/MorganCrouch/Documents/Github/CodeReviewSAMProj/CodeReviewFunction" \
                    "/Testing/Fixtures/SDO_pickled_soups.txt"
    with open(file_location, 'wb') as file:
        pickle.dump(results, file)


def determine_object_type(object_name, soup_object: BeautifulSoup):
    """
    Determine if a Object is a Wrapper, Base, or Base for Surface Automation.

    Used so that Considerations can change their behaviour based on how the Object is laid out.

    Returns:
        str: Type of object as 'Wrapper', 'Surface Automation Base' or 'Base' from Settings.OBJECT_TYPES
        bool: Object type estimated. True if Object type not given in the Object's name
    """
    if 'base' in object_name:
        # Check if Object has a Read stage for 'Read Image'
        read_stages = soup_object.find_all('stage', type='Read', recursive=False)
        for read_stage in read_stages:
            steps = read_stage.find_all('step', recursive=False)
            if steps:
                for step in steps:
                    step_name = step.action.id.string
                    if step_name == 'ReadBitmap':
                        return Settings.OBJECT_TYPES['surface auto base'], False
        else:
            # Otherwise assume not Surface Automation
            return Settings.OBJECT_TYPES['base'], False

    elif 'wrapper' in object_name:
        return Settings.OBJECT_TYPES['wrapper'], False

    # Object name contains neither 'Base' nor 'Wrapper'
    else:
        application_modeller = soup_object.find('appdef', recursive=False)
        # Object has an App Model
        # apptypeinfo only exists after running the App Modeller Wizard
        if application_modeller.apptypeinfo:

            # Check if the App Model only has empty elements
            if application_modeller.element.find('element') is None:
                return Settings.OBJECT_TYPES['wrapper'], True

            # Find all the Action stages and all subsheets (Action pages) in an Object.
            # Checks to see if there are more Actions per page than the cut off ratio, suggesting it's a wrapper.
            subsheets = soup_object.find_all('subsheet', recursive=False)
            action_stages = soup_object.find_all('stage', type='Action', recursive=False)
            if len(action_stages) >= len(subsheets) * Settings.ACTIONS_PER_PAGE_WRAPPER_RATIO:
                return Settings.OBJECT_TYPES['wrapper'], True
            else:
                return Settings.OBJECT_TYPES['base'], True

        # No Application Model exists indicating wrapper
        else:
            # Check for if the app model is inherited from another Object
            inherits_app_model = soup_object.find('parentobject', recursive=False)
            if inherits_app_model:
                return Settings.OBJECT_TYPES['base'], False

            # App model not inherited so none exists
            else:
                # Check if Object has a Read stage for 'Read Image'
                read_stages = soup_object.find_all('stage', type='Read', recursive=False)
                for read_stage in read_stages:
                    steps = read_stage.find_all('step', recursive=False)
                    if steps:
                        for step in steps:
                            step_name = step.action.id.string
                            if step_name == 'ReadBitmap':
                                return Settings.OBJECT_TYPES['surface auto base'], True

                # Otherwise assume not Surface Automation
                else:
                    return Settings.OBJECT_TYPES['wrapper'], True


def get_object_actions(object_soup: BeautifulSoup):
    """Go through a Beautiful Soup of a single BP Object's XML and extracts all Action names

    :param object_soup: BS4 Object for a single object.
    :return (list of str): List of Actions within the BP Object.
    """
    object_actions = []

    soup_actions = object_soup.find_all("subsheet")
    for action in soup_actions:
        action_name = action.next_element.string
        if action_name != 'Clean Up':
            object_actions.append(action.next_element.string)

    return object_actions