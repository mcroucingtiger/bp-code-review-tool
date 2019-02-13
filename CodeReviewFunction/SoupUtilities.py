import pickle
import time
from multiprocessing import Pool
from bs4 import BeautifulSoup, SoupStrainer
from . import Settings


def determine_object_type(object_name, soup_object: BeautifulSoup):
    """Determine if a Object is a Wrapper, Base, or Base for Surface Automation.

    Used so that Considerations can change their behaviour based on how the Object is laid out.

    Returns:
        str: Type of object as 'Wrapper', 'Surface Automation Base' or 'Base'
        bool: Object type estimated. True if Object type not given in the name

    """
    if 'base' in object_name:
        # Check if Object has a Read stage for 'Read Image'
        read_stages = soup_object.find_all('stage', type='Read', recursive=False)
        for read_stage in read_stages:
            steps = read_stage.find_all('step', recursive=False)
            for step in steps:
                step_name = step.action.id.string
                if step_name == 'ReadBitmap':
                    return Settings.OBJECT_TYPES['surface auto base'], False
        # Otherwise assume not Surface Automation
        return Settings.OBJECT_TYPES['base'], False

    elif 'wrapper' in object_name:
        return Settings.OBJECT_TYPES['wrapper'], False

    # Object name contains neither 'Base' nor 'Wrapper'
    else:
        application_modeller = soup_object.find('appdef', recursive=False)
        # apptypeinfo only exists after running the App Modeller Wizard
        if not application_modeller.apptypeinfo:
            # Check for if the app model is inherited from another Object
            inherits_app_model = soup_object.find('parentobject', recursive=False)
            if inherits_app_model:
                return Settings.OBJECT_TYPES['base'], False
            else:
                # Check if Object has a Read stage for 'Read Image'
                read_stages = soup_object.find_all('stage', type='Read', recursive=False)
                for read_stage in read_stages:
                    steps = read_stage.find_all('step', recursive=False)
                    for step in steps:
                        step_name = step.action.id.string
                        if step_name == 'ReadBitmap':
                            return Settings.OBJECT_TYPES['surface auto base'], True
                # Otherwise assume not Surface Automation
                return Settings.OBJECT_TYPES['wrapper'], True

        # If it an Application Model then it must be a Base
        else:
            return Settings.OBJECT_TYPES['base'], True


def extract_pickled_soups(xml_string) -> list:
    """Turn the xml into a list of pickled soups containing processes, objects, queues and the metadata.

    Uses multiprocessing to convert the full XML into multiple pickled bs4 objects to improve pocessing speed.
    To send data to/from pool processes, objects must be pickled. bs4 objects cannot be pickled, so process return the
    bs4 objects as pickled versions of the string form of bs4 soup objects.
    """
    pool = Pool(4)
    strainers = ['process', 'object', 'work-queue', 'header']
    soup_data = [(strainer, xml_string) for strainer in strainers]  # pool.starmap requires an iterable of tuples
    print("Multi-processing xml")
    start = time.clock()
    results = pool.starmap(extract_soup_from_xml, soup_data)
    pool.close()
    pool.join()
    end = time.clock()
    print('Time to multi-process xml: ' + str(end - start))

    #pickle_results_list(results)
    return results


def extract_soup_from_xml(strainer_param, xml_string):
    """Create a single soup object from the full xml_string and return it in str form.

    This function is called multiple times in parallel by the multi-processing pool.starmap"""
    individual_soup_str = None
    if strainer_param == 'header':
        soup_strainer = SoupStrainer(strainer_param)
        individual_soup = BeautifulSoup(xml_string, 'lxml', parse_only=soup_strainer)
        individual_soup_str = str(individual_soup)

    elif strainer_param == 'process' or strainer_param == 'work-queue':
        soup_strainer = SoupStrainer(strainer_param, xmlns=True)
        individual_soup = BeautifulSoup(xml_string, 'lxml', parse_only=soup_strainer)
        individual_soup_str = str(individual_soup)
    elif strainer_param == 'object':
        soup_strainer = SoupStrainer('process', {"type": "object"})
        individual_soup = BeautifulSoup(xml_string, 'lxml', parse_only=soup_strainer)
        individual_soup_str = str(individual_soup)

    return individual_soup_str


# Testing only
def pickle_results_list(results):
    """Pickle the results list and save to a file to skip this step when testing"""
    file_location = "C:/Users/MorganCrouch/Documents/Github/CodeReviewSAMProj/CodeReviewFunction" \
                    "/Testing/Fixtures/LAMP_pickled_soups.txt"
    with open(file_location, 'wb') as file:
        pickle.dump(results, file)


