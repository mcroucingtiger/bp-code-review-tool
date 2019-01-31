import logging
import azure.functions as func
from bs4 import BeautifulSoup
from bs4 import SoupStrainer
import json
import time
from multiprocessing import Pool
from collections import namedtuple
from .ReportPage import ReportPage, Result
from .Considerations.ObjectConsiderations import object_consideration_module_classes
from .Considerations.ProcessConsiderations import process_consideration_module_classes

# logging.critical .error .warning .info .debug
logging.info("CodeReview module running")
Sub_Soup = namedtuple('Sub_Soup', 'processes, objects, queues, metadata')


def test_with_local():
    print("Local testing running")
    report_pages = []
    print("Getting release off desktop")

    release_path_ = "C:/Users/MorganCrouch/Documents/Github/CodeReviewSAMProj/Test Releases/Multi-Object_Process.bprelease"
    release_path_ = "C:/Users/MorganCrouch/Documents/Reveal Group/Auto Code Review/" \
                   "Test Releases Good/MI Premium Payments - Backup Release v2.0.bprelease"
    release_path = "C:/Users/MorganCrouch/Documents/Reveal Group/Auto Code Review/" \
                    "Test Releases Good/LAMP - Send Correspondence_V01.01.01_20181214.bprelease"
    release_path_ = "C:/Users/MorganCrouch/Desktop/Testing Release.bprelease"

    xml_string = get_local_xml(release_path)

    # Use the extracted XML to create the report
    if xml_string:
        sub_soups = make_all_soups(xml_string)  # Parse the XML into multiple BeautifulSoup Objects

        # Delete after testing
        try:
            metadata = extract_metadata(sub_soups.metadata)
            object_considerations, process_considerations = get_active_considerations(metadata)
        except:
            print("Unable to find the header in the XML")

        # print(sub_soups.objects.prettify())

        for object_tag in sub_soups.objects:
            report_page_dict = make_report_object(object_tag, object_considerations, metadata)
            report_pages.append(report_page_dict)

        for process_tag in sub_soups.processes:
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
        sub_soups = make_all_soups(xml_string)  # Parse the XML into multiple BeautifulSoup Objects
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


def make_all_soups(xml_string) -> Sub_Soup:
    """Turn the xml into a named tuple of BeautifulSoup objects for all processes, objects, queues and the metadata.

    Uses multiprocessing to convert the full XML into multiple bs4 objects to improve speed. To send data to/from
    pool processes, data must be pickled. bs4 objects cannot be pickled, so process recieved the object as a string and
    converts back to BeautifulSoup after multiprocessing complete.

    Returns a Sub_Soup named tupple object defined at the top of the module.
    """
    pool = Pool(4)
    strainers = ['process', 'object', 'work-queue', 'header']
    soup_data = [(strainer, xml_string) for strainer in strainers]  # pool.starmap requires an iterable of tuples
    print("multi-processing")
    start = time.clock()
    results = pool.starmap(extract_soup, soup_data)
    pool.close()
    pool.join()
    end = time.clock()
    print('With multi ' + str(end - start))

    start = time.clock()
    print('decoding to BS4 objects')

    soups = []
    for i in range(4):
        if i == 1:
            soups.append(BeautifulSoup(results[i], 'lxml', parse_only=SoupStrainer('process', {"type": "object"})))
        else:
            soups.append(BeautifulSoup(results[i], 'lxml', parse_only=SoupStrainer(xmlns=True)))


    print(soups[1])
    end = time.clock()
    print('back to bs4: ' + str(end - start))

    return Sub_Soup(soups[0], soups[1], soups[2], soups[3])
    # start = time.clock()
    # print('make soups running')
    # only_metadata = SoupStrainer('header')
    # soup_metadata = BeautifulSoup(xml_string, 'lxml', parse_only=only_metadata)
    #
    # end = time.clock()
    # print('metadata ' + str(end - start))
    #
    # start = time.clock()
    # only_objects = SoupStrainer('process', {"type": "object"})
    # soup_objects = BeautifulSoup(xml_string, 'lxml', parse_only=only_objects)
    # soup_metadata_str = str(soup_objects)
    #
    # end = time.clock()
    # print('When finding object type ' + str(end - start))
    #
    # start = time.clock()
    # only_processes = SoupStrainer('process', xmlns=True)
    # soup_processes = BeautifulSoup(xml_string, 'lxml', parse_only=only_processes)
    # end = time.clock()
    # print('When finding full process ' + str(end - start))
    #
    # start = time.clock()
    # only_work_queue = SoupStrainer('work-queue', xmlns=True)
    # soup_queue = BeautifulSoup(xml_string, 'lxml', parse_only=only_work_queue)
    # end = time.clock()
    # print('When finding full queue ' + str(end - start))
    #
    # return Sub_Soup(soup_processes, soup_objects, soup_queue, soup_metadata)


def extract_soup(strainer_param, xml_string):
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
    # 'if' statements are for the scoring of individual modules that have any errors.

    current_object = soup_object.get('name').lower()

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
