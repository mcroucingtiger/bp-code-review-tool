import logging
import azure.functions as func
from bs4 import BeautifulSoup, SoupStrainer
import json
import time
from collections import namedtuple
from . import SoupUtilities
from .ReportPage import ReportPage
from .Considerations.ObjectConsiderations import object_consideration_module_classes
from .Considerations.ProcessConsiderations import process_consideration_module_classes

# logging.critical .error .warning .info .debug
logging.info("CodeReview module running")
Sub_Soup = namedtuple('Sub_Soup', 'processes, objects, queues, metadata')


def main(req: func.HttpRequest) -> func.HttpResponse:
    print("Main running")
    xml_string = ''
    report_pages = []
    logging.info("Python HTTP trigger function processed a request.")

    try:
        logging.info("Attempting to get the body")
        req_body = req.get_body()
        xml_string = req_body
    except ValueError:
        logging.error("Unable to access request body")
        pass

    # Use the extracted XML to create the report
    if xml_string:
        sub_soups = SoupUtilities.extract_pickled_soups(xml_string)  # Parse the XML into multiple BeautifulSoup Objects
        metadata = extract_metadata(sub_soups.metadata)
        object_considerations, process_considerations = get_active_considerations(metadata)

        for object_tag in sub_soups.objects.contents:
            report_page_dict = make_report_object(object_tag, object_considerations, metadata)
            report_pages.append(report_page_dict)

        for process_tag in sub_soups.processes.contents:
            report_page_dict = make_report_process(process_tag, process_considerations, metadata)
            report_pages.append(report_page_dict)

        report_page_dict = make_report_settings_page(metadata)
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

# --- TESTING ONLY ---
def test_with_local():
    print("Local testing running")
    report_pages = []
    print("Getting release off desktop")

    # Releases with Header
    release_path_ = "C:/Users/MorganCrouch/Documents/Github/CodeReviewSAMProj/CodeReviewFunction" \
                    "/Testing/SAM Processed XML/LAMP.xml"
    release_path = "C:/Users/MorganCrouch/Documents/Github/CodeReviewSAMProj/CodeReviewFunction" \
                    "/Testing/SAM Processed XML/MERS.xml"
    release_path_ = "C:/Users/MorganCrouch/Documents/Github/CodeReviewSAMProj/CodeReviewFunction" \
                    "/Testing/SAM Processed XML/MI Report.xml"
    release_path_ = "C:/Users/MorganCrouch/Documents/Github/CodeReviewSAMProj/CodeReviewFunction" \
                   "/Testing/SAM Processed XML/Multi-Process.xml"
    release_path_ = "C:/Users/MorganCrouch/Documents/Github/CodeReviewSAMProj/CodeReviewFunction" \
                   "/Testing/SAM Processed XML/SDO Surface Auto.xml"
    release_path_ = "C:/Users/MorganCrouch/Documents/Github/CodeReviewSAMProj/CodeReviewFunction" \
                   "/Testing/SAM Processed XML/Fiserv Current.xml"



    xml_string = get_local_xml(release_path)

    if xml_string:
        # Parse the XML into multiple BeautifulSoup Objects
        sub_soups = SoupUtilities.extract_pickled_soups(xml_string)

        # --- Delete after testing
        # try:
        metadata = extract_metadata(sub_soups.metadata)
        active_object_consid_classes, active_process_consid_classes = get_active_considerations(metadata)
        # except:
        print("!!! Unable to find the header in the XML !!!")  # Only for testing

        # print(sub_soups.objects.prettify())
        start_processing = time.clock()
        for object_tag in sub_soups.objects:
            report_page_dict = make_report_object(object_tag, active_object_consid_classes, metadata)
            report_pages.append(report_page_dict)

        for process_tag in sub_soups.processes:
            report_page_dict = make_report_process(process_tag, active_process_consid_classes, metadata)
            report_pages.append(report_page_dict)

        report_page_dict = make_report_settings_page(metadata)
        report_pages.append(report_page_dict)

        json_report = json.dumps(report_pages)
        print(json_report)
        print("\nProcessing Time: " + str(time.clock() - start_processing))

    else:
        print("XML wasn't read")


def get_local_xml(path):
    if path:
        release_path = path
    else:
        release_path = "C:/Users/MorganCrouch/Documents/Reveal Group/Auto Code Review/" \
                       "Test Releases Good/MI Premium Payments - Backup Release v2.0.bprelease"

    with open(release_path, "r", encoding="utf8") as file:
        xml_string = file.read()
    return xml_string


def deserialize_to_soup(results):
    """Convert the pickled strings into bs4 soup objects and returns it as a named tuple of type Sub_Soup."""
    start = time.clock()
    print('Deserialize to soups')
    soups = []
    for i in range(4):
        if i == 1:
            soups.append(BeautifulSoup(results[i], 'lxml', parse_only=SoupStrainer('process', {"type": "object"})))
        else:
            soups.append(BeautifulSoup(results[i], 'lxml', parse_only=SoupStrainer(xmlns=True)))
    end = time.clock()
    print('Time to convert to bs4: ' + str(end - start))

    # return Sub_Soup(soup_processes, soup_objects, soup_queue, soup_metadata)
    return Sub_Soup(soups[0], soups[1], soups[2], soups[3])


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
    """Create lists containing consideration metaclasses for all active object and process considerations.

    Goes through config file for all considerations marked as active. Then compares these active considerations
    to the considerations available within this script.

    The object_consideration_classes and process_consideration_classes will contain a list of metaclasses
    of the Consideration's class. Only considerations that are marked as 'Active' in the config file
    will have their class' metaclass added to the respective active_process_consideration_classes or
    active_object_consideration_classes list.
    """

    active_object_consideration_classes = []
    active_process_consideration_classes = []

    active_considerations_object = metadata['active considerations object']
    active_considerations_process = metadata['active considerations process']
    object_consideration_classes = object_consideration_module_classes()
    process_consideration_classes = process_consideration_module_classes()

    # Retrieve active Object Considerations
    for consideration_status_dict in active_considerations_object:
        if consideration_status_dict['Active']:  # Consideration is active from metadata
            report_consideration_name = consideration_status_dict['Object Considerations']
            for object_class in object_consideration_classes:
                class_consideration_name = object_class[1].CONSIDERATION_NAME
                if class_consideration_name == report_consideration_name:
                    # Add  metaclass and add to object consideration list
                    active_object_consideration_classes.append(object_class[1])
                    break

    # TODO: Test function once process side of report is built
    # Retrieve active Object Considerations
    for consideration_status_dict in active_considerations_process:
        if consideration_status_dict['Active']:  # Consideration is active
            report_consideration_name = consideration_status_dict['Process Considerations']
            for process_class in process_consideration_classes:
                class_consideration_name = process_class[1].CONSIDERATION_NAME
                if class_consideration_name == report_consideration_name:
                    # Adds  metaclass to process consideration list
                    active_process_consideration_classes.append(process_class[1])
                    break

    return active_object_consideration_classes, active_process_consideration_classes


# Still in dev
def make_report_process(soup_process, active_process_considerations_classes, metadata):
    """Use the filtered soup of a single process tag element to generate the JSON for a page in the report."""
    report_page = ReportPage()
    report_page.set_page_header_info('Process', soup_process)

    logging.info("Running make_report_process function for " + report_page.page_name)

    # TODO: fill out process side

    return report_page.get_page_as_dict()


def make_report_object(soup_object, active_object_consideration_classes, metadata):
    """Use the filtered soup of a single object tag element to generate the JSON for a object page in the report."""
    report_page = ReportPage()

    current_object_name = soup_object.get('name').lower()
    object_type, evaluated = SoupUtilities.determine_object_type(current_object_name, soup_object)
    metadata['object type'] = object_type
    report_page.set_page_header_info('Object', soup_object, object_type, evaluated)

    logging.info("Running make_report_object function for " + report_page.page_name)

    blacklist_objects = metadata['blacklist']
    metadata_active_objects = metadata['active considerations object']

    for object_consideration in active_object_consideration_classes:
        # Check the Object name isn't a blacklisted object
        if not any(ignored_object in current_object_name for ignored_object in blacklist_objects):
            for active_object in metadata_active_objects:
                # Find current consideration in the active consideration info of config file
                if active_object['Object Considerations'] == object_consideration.CONSIDERATION_NAME:
                    # Check if forced result was set in config and apply it
                    force_result = active_object['Force Result']
                    score_scale = active_object['Score Scale']

                    temp_consideration = object_consideration()
                    if force_result == score_scale == '':
                        temp_consideration.check_consideration(soup_object, metadata)
                        temp_consideration.evaluate_score_and_result()
                    else:
                        temp_consideration.evaluate_score_and_result(float(score_scale), force_result)
                    temp_consideration.add_to_report(report_page)

    return report_page.get_page_as_dict()


def make_report_settings_page(metadata):
    """Add a setting report page where 'Report Considerations' are the settings to be sent to Blue Prism."""
    report_page = ReportPage()
    report_page.set_page_header_info('Settings', None)
    logging.info("Running make_report_object function for Settings")
    for setting in metadata['settings']:
        report_page.considerations.append(setting)

    return report_page.get_page_as_dict()


if __name__ == '__main__':
    test_with_local()


