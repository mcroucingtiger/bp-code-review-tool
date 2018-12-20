from bs4 import SoupStrainer
from SharedCode.ReportPageHelper import ReportPageHelper as RH
from SharedCode.Considerations.ObjectConsiderations import *
import json
from collections import namedtuple

print("Local testing page started")
release_path = "C:/Users/MorganCrouch/Documents/Github/CodeReviewSAMProj/Test Releases/Multi-Object_Process.bprelease"
Sub_Soup = namedtuple('Sub_Soup', 'processes, objects, queues')

def has_attr_bpversion(tag):
    """Only Objects have an attribute called bpversion. This filter function should return all the Object tags"""
    return tag.has_attr('bpversion')


def get_local_xml_soup() -> BeautifulSoup:
    infile = open(release_path, "r")
    contents = infile.read()

    print('\nObjects:')
    only_objects = SoupStrainer('object', xmlns=True)
    soup_objects = BeautifulSoup(contents, 'lxml', parse_only=only_objects)
    for object_tag in soup_objects.contents:
        print(object_tag.get('name'))

    print('\nProcesses:')
    only_processes = SoupStrainer('process', xmlns=True)
    soup_processes = BeautifulSoup(contents, 'lxml', parse_only=only_processes)
    for process_tag in soup_processes.contents:
        print(process_tag.get('name'))

    print('\nQueue:')
    only_work_queue = SoupStrainer('work-queue', xmlns=True)
    soup_queue = BeautifulSoup(contents, 'lxml', parse_only=only_work_queue)
    for queue_tag in soup_queue.contents:
        print(queue_tag.get('name'))

    return soup_objects

def make_soups(xml_string) -> Sub_Soup:
    """Turns the xml into a named tuple of BeautifulSoup objects for all processes, objects and queues"""
    # Look at Local testing script to see how access names
    only_objects = SoupStrainer('object', xmlns=True)
    soup_objects = BeautifulSoup(xml_string, 'lxml', parse_only=only_objects)

    only_processes = SoupStrainer('process', xmlns=True)
    soup_processes = BeautifulSoup(xml_string, 'lxml', parse_only=only_processes)

    only_work_queue = SoupStrainer('work-queue', xmlns=True)
    soup_queue = BeautifulSoup(xml_string, 'lxml', parse_only=only_work_queue)

    return Sub_Soup(soup_processes, soup_objects, soup_queue)

def check_system_exceptions():
    error_list = []
    logging.info("'Check System Exception' function called")

    soup = get_local_xml_soup()
    # Finding the 'exception stage name' and 'page name' for all exception stages with empty an exception detail field
    exception_stages = soup.find_all('exception')

    for exception_stage in exception_stages:
        if not exception_stage.get('detail') and not exception_stage.get('usecurrent'):
            exception_name = exception_stage.parent.get('name')
            parent_subsheet_id = exception_stage.parent.subsheetid.string
            exception_page = soup.find('subsheet', {'subsheetid': parent_subsheet_id}).contents[1].string

            error = {
                "Exception name": exception_name,
                "Exception page": exception_page
            }
            error_list.append(error)

    # Printing error statement to the console (temporary)

    jsonfile = json.dumps(error_list)
    print(jsonfile)
    for error in error_list:
        print("Exception stage '%s' on page '%s' is missing an Exception Detail."
                     % (error["Exception name"], error["Exception page"]))

def tester_json2():
    print("sorry?")
    rh = ReportPageHelper()
    topic = "Exception Handling"
    consideration = "Exception Message not exist"''
    rh.set_topic(topic)
    rh.set_consideration(topic, consideration)

    topic = "Naming Convention"
    rh.set_topic(topic)

    consideration = "Stage starts with verb"
    rh.set_consideration(topic, consideration)
    rh.set_error(topic, consideration, "error 1", "Main Page")
    rh.set_error(topic, consideration, "error 2", "Sub Page")

    consideration = "No Infinite Loops"
    rh.set_consideration(topic, consideration)
    rh.set_error(topic, consideration, "error 1", "Main page")
    rh.set_error(topic, consideration, "error 2", "Sub page")

    topic = "Object Stuff"
    rh.set_topic(topic)

    consideration = "Stage starts with verb"
    rh.set_consideration(topic, consideration)
    rh.set_error(topic, consideration, "error 1", "Main Page")
    rh.set_error(topic, consideration, "error 2", "Sub Page")

    consideration = "No Infinite Loops"
    rh.set_consideration(topic, consideration)
    rh.set_error(topic, consideration, "error 1", "Main Page")
    rh.set_error(topic, consideration, "error 2", "Sub Page")

    output_json = rh.get_report_json()
    print(output_json)


def attach_action_test():
    attach_found = False
    soup = get_local_xml_soup()
    subsheets = soup.find_all('subsheet')  # Find all page names
    for subsheet in subsheets:
        if subsheet.contents[1].string.lower().find("attach") >= 0:  # A page has the work 'Attach' in it
            attach_found = True


def set_actions(object_soup: BeautifulSoup):
    actions = object_soup.find_all("subsheet")
    print("\n---\n")
    for action in actions:
        print(action.next_element.string)
    pass


def get_name(object_soup):
    print("\n---\n")
    print(object_soup.contents[0].get('name'))


def check_business_obj_has_attach(soup: BeautifulSoup, report_helper: ReportPageHelper):
    logging.info("'Check Business Obj Has Attach' function called")
    report_helper.set_consideration(ConsiderationsList.CHECK_OBJ_HAS_ATTACH)

    attach_found = False
    subsheets = soup.find_all('subsheet')  # Find all page names
    for subsheet in subsheets:
        if subsheet.next_element.string.lower().find("attach") >= 0:  # A page has the work 'Attach' in it
            attach_found = True
            break

    if not attach_found:
        report_helper.set_error(ConsiderationsList.CHECK_OBJ_HAS_ATTACH,
                                "Unable to find and an Attach page within the Object")

def check_actions_use_attach(soup: BeautifulSoup, report_helper: ReportPageHelper):
    logging.info("'Check System Exception' function called")
    report_helper.set_consideration(ConsiderationsList.CHECK_ACTIONS_USE_ATTACH)

    


sub_group = make_soups(get_local_xml_soup())
for soup_object in sub_group.objects:
    check_business_obj_has_attach(soup_object, RH())















