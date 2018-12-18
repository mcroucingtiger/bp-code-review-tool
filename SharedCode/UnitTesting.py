from bs4 import SoupStrainer
from SharedCode.ReportPageHelper import *
from SharedCode.Considerations.ObjectConsiderations import *

print("Local testing page started")
release_path = "C:/Users/MorganCrouch/Documents/Github/CodeReviewSAMProj/SharedCode/Multi-Object_Process.bprelease"

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




get_name(get_local_xml_soup())







