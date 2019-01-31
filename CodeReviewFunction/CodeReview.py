import logging
import azure.functions as func
from bs4 import BeautifulSoup
from bs4 import SoupStrainer
import json
import time
from multiprocessing import Pool, Queue, Process
import dill
import pickle
from multiprocessing import cpu_count
from collections import namedtuple
from .ReportPage import ReportPage, Result
from .Considerations.ObjectConsiderations import object_consideration_module_classes
from .Considerations.ProcessConsiderations import process_consideration_module_classes

# logging.critical .error .warning .info .debug
logging.info("CodeReview module running")
Sub_Soup = namedtuple('Sub_Soup', 'processes, objects, queues, metadata')
xml_string_global = 'a'

def get_local_xml(path):

    if path:
        release_path = path
    else:
        release_path = "C:/Users/MorganCrouch/Documents/Reveal Group/Auto Code Review/" \
                       "Test Releases Good/MI Premium Payments - Backup Release v2.0.bprelease"

    infile = open(release_path, "r")
    xml_string = infile.read()
    infile.close()
    return xml_string


def test_with_local():
    print("Local testing running")
    report_pages = []
    print("Getting release off desktop")

    release_path_ = "C:/Users/MorganCrouch/Documents/Github/CodeReviewSAMProj/Test Releases/Multi-Object_Process.bprelease"
    release_path_ = "C:/Users/MorganCrouch/Documents/Reveal Group/Auto Code Review/" \
                   "Test Releases Good/MI Premium Payments - Backup Release v2.0.bprelease"
    release_path = "C:/Users/MorganCrouch/Documents/Reveal Group/Auto Code Review/" \
                    "Test Releases Good/LAMP - Send Correspondence_V01.01.01_20181214.bprelease"

    xml_string = get_local_xml(release_path)

    # Use the extracted XML to create the report
    if xml_string:
        sub_soups = make_soups(xml_string)  # Parse the XML into multiple BeautifulSoup Objects

        metadata = extract_metadata(sub_soups.metadata)
        object_considerations, process_considerations = get_active_considerations(metadata)

        for object_tag in sub_soups.objects.contents:
            report_page_dict = make_report_object(object_tag, object_considerations, metadata)
            report_pages.append(report_page_dict)

        for process_tag in sub_soups.processes.contents:
            report_page_dict = make_report_process(process_tag, process_considerations, metadata)
            report_pages.append(report_page_dict)

        report_page_dict = make_report_settings(metadata)
        report_pages.append(report_page_dict)

        json_report = json.dumps(report_pages)
        print(json_report)

    else:
        print("XML wasn't read")


def main(req: func.HttpRequest) -> func.HttpResponse:
    print("Main running")
    xml_string = ''
    report_pages = []
    logging.info("Python HTTP trigger function processed a request.")

    try:
        req_body = req.get_body()
        xml_string = req_body
    except ValueError:
        logging.error("Unable to access request body")
        pass

    # Use the extracted XML to create the report
    if xml_string:
        sub_soups = make_soups(xml_string)  # Parse the XML into multiple BeautifulSoup Objects
        metadata = extract_metadata(sub_soups.metadata)
        object_considerations, process_considerations = get_active_considerations(metadata)

        for object_tag in sub_soups.objects.contents:
            report_page_dict = make_report_object(object_tag, object_considerations, metadata)
            report_pages.append(report_page_dict)

        for process_tag in sub_soups.processes.contents:
            report_page_dict = make_report_process(process_tag, process_considerations, metadata)
            report_pages.append(report_page_dict)

        report_page_dict = make_report_settings(metadata)
        report_pages.append(report_page_dict)

        json_report = json.dumps(report_pages)
        print(json_report)

        # Sends an HTTP response containing the full report information in JSON
        return func.HttpResponse(json_report)

    else:
        return func.HttpResponse(
            "Unable to read XML",
            status_code=400
        )


def create_soup(strainer_param):
    individual_soup_str = None
    xml_string = xml_string_global
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

def initializer(xml):
    global xml_string_global
    xml_string_global = xml

# TODO add multithreading here
def make_soups(xml_string) -> Sub_Soup:
    """Turn the xml into a named tuple of BeautifulSoup objects for all processes, objects and queues"""
    # NOTE: attempted to get multiprocessing working and failed. Issues/notes were:
    #   1. Dont mulit-thread, multi-process
    #   2. Can give access to the xml_string using global but dont know how to do this for
    #       queues (which i think can handle bigger objects?)
    #       https://thelaziestprogrammer.com/python/multiprocessing-pool-a-global-solution
    #   3. It processes the SoupStrainer fine enough, but the big issue is returning the BeautifulSoup object back
    #      to the main process. BeuatifulSoup objects cant be pickled as they always get recursive errors.
    #   4. Dont bother increasing the recursion limit. Doesnt seem to help.
    #

    pool = Pool(4, initializer, initargs=[xml_string])
    strainers = ['process', 'header', 'object', 'work-queue']
    #soup_data = [(strainer, xml_string) for strainer in strainers]  # pool.starmap requires an iterable of tuples
    print("multi-processing")
    start = time.clock()
    #results = pool.starmap(create_soup, soup_data)
    results = pool.map(create_soup, strainers)
    pool.close()
    pool.join()
    end = time.clock()
    print('With multi ' + str(end - start))
    start = time.clock()
    print('encoding to BS4 objects')
    r = [BeautifulSoup(x, 'lxml') for x in results]
    end = time.clock()
    print('back to bs4: ' + str(end - start))




    start = time.clock()
    print('make soups running')
    only_metadata = SoupStrainer('header')
    soup_metadata = BeautifulSoup(xml_string, 'lxml', parse_only=only_metadata)

    end = time.clock()
    print('metadata ' + str(end - start))

    start = time.clock()
    only_objects = SoupStrainer('process', {"type": "object"})
    soup_objects = BeautifulSoup(xml_string, 'lxml', parse_only=only_objects)
    soup_metadata_str = str(soup_objects)
    print(soup_metadata_str)
    re_soup = BeautifulSoup(soup_metadata_str, 'lxml')
    a = pickle.dumps(soup_metadata_str)
    end = time.clock()
    print('When finding object type ' + str(end - start))

    start = time.clock()
    only_processes = SoupStrainer('process', xmlns=True)
    soup_processes = BeautifulSoup(xml_string, 'lxml', parse_only=only_processes)
    end = time.clock()
    print('When finding full process ' + str(end - start))

    start = time.clock()
    only_work_queue = SoupStrainer('work-queue', xmlns=True)
    soup_queue = BeautifulSoup(xml_string, 'lxml', parse_only=only_work_queue)
    end = time.clock()
    print('When finding full queue ' + str(end - start))

    return Sub_Soup(soup_processes, soup_objects, soup_queue, soup_metadata)


def extract_metadata(soup_metadata: BeautifulSoup):
    """Take in the metadata XML and outputs a dict of the information."""
    metadata = {}

    # Get each JSON string from the header tag in the XML and parses the JSON string into a python data type.
    coversheet_info_str = soup_metadata.find('coversheetinformation').string
    metadata['coversheet info'] = json.loads(coversheet_info_str)

    additional_info_str = soup_metadata.find('additionalreleaseinformation').string
    metadata['additional info'] = json.loads(additional_info_str)

    blacklist_str = soup_metadata.find('blacklist').string
    metadata['blacklist'] = json.loads(blacklist_str)

    settings_str = soup_metadata.find('settings').string
    metadata['settings'] = json.loads(settings_str)

    active_considerations_process_str = soup_metadata.find('activeconsiderationsprocess').string
    metadata['active considerations process'] = json.loads(active_considerations_process_str)
    # Strip accidental whitespace from end of all consideration names so they match the name in each class
    for active_consideration in metadata['active considerations process']:
        active_consideration['Process Considerations'] = active_consideration['Process Considerations'].strip()

    active_considerations_object_str = soup_metadata.find('activeconsiderationsobject').string
    metadata['active considerations object'] = json.loads(active_considerations_object_str)
    # Strip accidental whitespace from end of all consideration names so they match the name in each class
    for active_consideration in metadata['active considerations object']:
        active_consideration['Object Considerations'] = active_consideration['Object Considerations'].strip()

    return metadata


def get_active_considerations(metadata):
    """Go through the config file and create lists for all active object and process considerations.

    The object_considerations and process_considerations will contain a list of instantiated objects
    of the Consideration class. Only considerations that are marked as 'Active' in the config file
    will have their class' object added to the respective object_considerations or process_considerations list.
    """

    object_considerations = []
    process_considerations = []

    active_considerations_object = metadata['active considerations object']
    active_considerations_process = metadata['active considerations process']
    object_consideration_classes = object_consideration_module_classes()
    process_consideration_classes = process_consideration_module_classes()

    # Retrieve active Object Considerations
    for consideration_status_dict in active_considerations_object:
        if consideration_status_dict['Active']:  # Consideration is active
            report_consideration_name = consideration_status_dict['Object Considerations']
            for object_class in object_consideration_classes:
                class_consideration_name = object_class[1].CONSIDERATION_NAME
                if class_consideration_name == report_consideration_name:
                    # Instantiate class and add to object to consideration list
                    object_considerations.append(object_class[1]())
                    break

    # TODO: Test function once process side of report is built
    # Retrieve active Object Considerations
    for consideration_status_dict in active_considerations_process:
        if consideration_status_dict['Active']:  # Consideration is active
            report_consideration_name = consideration_status_dict['Process Considerations']
            for process_class in process_consideration_classes:
                class_consideration_name = process_class[1].CONSIDERATION_NAME
                if class_consideration_name == report_consideration_name:
                    # Instantiate class and add to object to consideration list
                    process_considerations.append(process_class[1]())
                    break

    return object_considerations, process_considerations


def make_report_process(soup_process,process_considerations, metadata):
    """Use the filtered soup of a single process tag element to generate the JSON for a page in the report."""
    report_page = ReportPage()
    report_page.set_page_type('Process', soup_process)

    logging.info("Running make_report_process function for " + report_page.page_name)

    # TODO: fill out process side

    return report_page.get_page_as_dict()


def make_report_object(soup_object, object_considerations, metadata):
    """Use the filtered soup of a single object tag element to generate the JSON for a page in the report."""
    report_page = ReportPage()
    report_page.set_page_type('Object', soup_object)
    logging.info("Running make_report_object function for " + report_page.page_name)

    blacklist = metadata['blacklist']
    active_objects = metadata['active considerations object']

    # All modules intended for creating a object specific page in the report.
    # If statements are for the scoring of individual modules that any errors.

    current_object = soup_object.next_element.get('name').lower()

    for object_consideration in object_considerations:
        # Check the Object name isn't a blacklisted object
        if not any(ignored_object in current_object for ignored_object in blacklist):
            # Check to see if the Object abides by the current consideration
            object_consideration.check_consideration(soup_object)
            for active_object in active_objects:
                # Find current consideration in the active consideration info of config file
                if active_object['Object Considerations'] == object_consideration.CONSIDERATION_NAME:
                    # Check if forced result was set in config and apply it
                    force_result = active_object['Force Result']
                    score_scale = active_object['Score Scale']
                    if force_result == score_scale == '':
                        object_consideration.evaluate_score_and_result()
                    else:
                        object_consideration.evaluate_score_and_result(float(score_scale), force_result)
                    break

            object_consideration.add_to_report(report_page)

    return report_page.get_page_as_dict()


def make_report_settings(metadata):
    """Add a setting report page where 'Report Considerations' are the settings to be sent to Blue Prism."""
    report_page = ReportPage()
    report_page.set_page_type('Settings', None)
    logging.info("Running make_report_object function for Settings")
    for setting in metadata['settings']:
        report_page.considerations.append(setting)

    return report_page.get_page_as_dict()


if __name__ == '__main__':
    test_with_local()
