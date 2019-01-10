import logging
import azure.functions as func
from bs4 import BeautifulSoup
from bs4 import SoupStrainer
import json
import sys
from os import path
from collections import namedtuple
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from SharedCode.ReportPage import ReportPage, Result
from SharedCode.Considerations.ObjectConsiderations import CheckObjHasAttach, object_consideration_module_classes
from SharedCode.Considerations.ProcessConsiderations import process_consideration_module_classes


# logging.critical .error .warning .info .debug
logging.info("__init__ page running")
Sub_Soup = namedtuple('Sub_Soup', 'processes, objects, queues, metadata')


def main():#req: func.HttpRequest) -> func.HttpResponse:
    print("Main running")
    xml_string = ''
    report_pages = []
    logging.info("Python HTTP trigger function processed a request.")

    # try:
    #     req_body = req.get_body()
    #     xml_string = req_body
    # except ValueError:
    #     logging.error("Unable to access request body")
    #     pass

    # Testing only
    release_path = "C:/Users/MorganCrouch/Desktop/testing Release.bprelease"
    infile = open(release_path, "r")
    xml_string = infile.read()

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


def make_soups(xml_string) -> Sub_Soup:
    """Turn the xml into a named tuple of BeautifulSoup objects for all processes, objects and queues"""
    only_metadata = SoupStrainer('header')
    soup_metadata = BeautifulSoup(xml_string, 'lxml', parse_only=only_metadata)

    only_objects = SoupStrainer('object', xmlns=True)
    soup_objects = BeautifulSoup(xml_string, 'lxml', parse_only=only_objects)

    only_processes = SoupStrainer('process', xmlns=True)
    soup_processes = BeautifulSoup(xml_string, 'lxml', parse_only=only_processes)

    only_work_queue = SoupStrainer('work-queue', xmlns=True)
    soup_queue = BeautifulSoup(xml_string, 'lxml', parse_only=only_work_queue)

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


main()
