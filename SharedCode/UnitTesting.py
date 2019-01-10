

from SharedCode.ReportPage import ReportPage
from bs4 import SoupStrainer
from bs4 import BeautifulSoup
from SharedCode.Considerations.ObjectConsiderations import *
import json
import time
from collections import namedtuple

print("Local testing page started")
_release_path = "C:/Users/MorganCrouch/Documents/Github/CodeReviewSAMProj/Test Releases/Multi-Object_Process.bprelease"
_release_path = "C:/Users/MorganCrouch/Documents/Reveal Group/Auto Code Review/" \
               "Test Releases Good/MI Premium Payments - Backup Release v2.0.bprelease"
release_path = "C:/Users/MorganCrouch/Documents/Reveal Group/Auto Code Review/" \
               "Test Releases Good/LAMP - Send Correspondence_V01.01.01_20181214.bprelease"
Sub_Soup = namedtuple('Sub_Soup', 'processes, objects, queues')


def has_attr_bpversion(tag):
    """Only Objects have an attribute called bpversion. This filter function should return all the Object tags"""
    return tag.has_attr('bpversion')


def get_local_xml_soups() -> BeautifulSoup:
    """Gets and converts local XML into Beautiful Soup objects"""
    infile = open(release_path, "r")
    contents = infile.read()

    print('\nObjects:')
    start = time.clock()
    only_objects = SoupStrainer('object', xmlns=True)
    soup_objects = BeautifulSoup(contents, 'lxml', parse_only=only_objects)
    for object_tag in soup_objects.contents:
        print(object_tag.get('name'))
    end = time.clock()
    print(end - start)

    print('\nProcesses:')
    start = time.clock()
    only_processes = SoupStrainer('process', xmlns=True)
    soup_processes = BeautifulSoup(contents, 'lxml', parse_only=only_processes)
    for process_tag in soup_processes.contents:
        print(process_tag.get('name'))
    end = time.clock()
    print(end - start)

    print('\nQueue:')
    start = time.clock()
    only_work_queue = SoupStrainer('work-queue', xmlns=True)
    soup_queue = BeautifulSoup(contents, 'lxml', parse_only=only_work_queue)
    for queue_tag in soup_queue.contents:
        print(queue_tag.get('name'))
    end = time.clock()
    print(end - start)

    return Sub_Soup(soup_processes, soup_objects, soup_queue)


def attach_action_test():
    attach_found = False
    soup = get_local_xml_soups()
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


def check_consideration(soup: BeautifulSoup) -> list:
    """Check if an Object starts with Attach action."""
    blacklist_attach_actions = ['launch', 'close', 'terminate', 'attach', 'initialise', 'clean up', 'detach']
    blacklist_object_names = ['wrapper']

    object_name = soup_object.next_element.get('name').lower()
    # Current Object name not blacklisted
    # TODO pretty sure its still not ignoring
    if not any(blacklist_word in object_name for blacklist_word in blacklist_object_names):
        # Iterate over all Actions in the Object
        subsheets = soup.find_all('subsheet') # TODO this can turn off recursive?
        for subsheet in subsheets:
            action_name = subsheet.next_element.string.lower()
            # Check the Action does not contain a word from the blacklist
            if not any(blacklist_action in action_name for blacklist_action in blacklist_attach_actions):
                print("Not blacklisted - " + subsheet.next_element.string )
                if not _action_begins_attach(subsheet, soup):
                    print("Action failed - " + subsheet.next_element.string)
                    #print("Action doesn't begin with an attach")

                    ...  # Add error to the report page helper
                else:
                    # print("Action begins with an attach")
                    pass
    else:
        # Add error that object was blacklisted but force max score and result of Not Applicable
        ...


def _action_begins_attach(subsheet, soup):
    """Return True an Action's page starts with an Attach page stage"""
    start_time = time.clock()
    # TODO: Optimise searching, potentially use soup strained
    subsheet_id = subsheet.get('subsheetid')
    # Gets all start stages in the object
    start_stages = soup.find_all('stage', type='Start')  # TODO: also find where subsheetid matches current. Probs need to turn recursive off where possible
    for start_stage in start_stages:
        # Finds the start stage of the current Action
        if start_stage.next_element.string == subsheet_id:
            start_onsuccess = start_stage.find('onsuccess').string
            page_reference_stages = soup.find_all('stage', type='SubSheet')
            for page_reference_stage in page_reference_stages:
                # Check if a Page reference stage is the first step in the Action after start stage
                if page_reference_stage.get('stageid') == start_onsuccess:
                    if 'attach' in page_reference_stage.get('name').lower():
                        end_time = time.clock()
                        print(end_time - start_time)
                        return True

    end_time = time.clock()
    print(end_time - start_time)
    return False

sub_group = get_local_xml_soups()
for soup_object in sub_group.objects:
    object_name = soup_object.next_element.get('name')
    print('\n=== Current Object: ' + object_name + " ===")
    check_consideration(soup_object)


