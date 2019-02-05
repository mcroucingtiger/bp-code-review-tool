from bs4 import BeautifulSoup
import time
from ..CodeReview import extract_pickled_soups, get_local_xml, deserialize_to_soup
import pickle
from ..Considerations.ObjectConsiderations import *
from ..Considerations.ProcessConsiderations import *

print("Local unit testing page started")

_release_path = "C:/Users/MorganCrouch/Documents/Github/CodeReviewSAMProj/Test Releases/Multi-Object_Process.bprelease"
_release_path = "C:/Users/MorganCrouch/Documents/Reveal Group/Auto Code Review/" \
               "Test Releases Good/MI Premium Payments - Backup Release v2.0.bprelease"
_release_path = "C:/Users/MorganCrouch/Documents/Reveal Group/Auto Code Review/" \
               "Test Releases Good/LAMP - Send Correspondence_V01.01.01_20181214.bprelease"
_release_path = "C:/Users/MorganCrouch/Documents/Reveal Group/Auto Code Review/Test Releases Good/MERS v1.0.bprelease"
_release_path = "C:/Users/MorganCrouch/Desktop/Testing Release.bprelease"
release_path = "C:/Users/MorganCrouch/Desktop/test.bprelease"

def has_attr_bpversion(tag):
    """Only Objects have an attribute called bpversion. This filter function should return all the Object tags"""
    return tag.has_attr('bpversion')


def print_sub_soups_contents(sub_soups):
    print('\nObjects:')
    for object_tag in sub_soups.objects:
        print(object_tag.get('name'))
    print('\nProcesses:')
    for process_tag in sub_soups.processes:
        print(process_tag.get('name'))
    print('\nQueue:')
    for queue_tag in sub_soups.queues:
        print(queue_tag.get('name'))


def print_actions_in_objectsoup(object_soup: BeautifulSoup):
    actions = object_soup.find_all("subsheet")
    print("\n---\n")
    for action in actions:
        print(action.next_element.string)
    pass


def print_name_objectsoup(object_soup):
    print("\n---\n")
    print(object_soup.contents[0].get('name'))


def get_local_pickled_results():
    """Get results list from the pickled version saved in file"""
    file_location = 'C:/Users/MorganCrouch/Documents/Github/CodeReviewSAMProj/CodeReviewFunction' \
                    '/Testing/Fixtures/results_big_testing.txt'
    with open(file_location, 'rb') as file:
        results = pickle.load(file)
    return results


if __name__ == '__main__':
    print('__main__ running for UnitTesting')
    full_speed_start = time.clock()

    # --- To Use Raw XML ---
    sub_soups = deserialize_to_soup(extract_pickled_soups(get_local_xml(release_path)))

    # -- To Use Pre-Pickled ---
    # pickled_results = get_local_pickled_results()
    # sub_soups = deserialize_to_soup(pickled_results)

    print_sub_soups_contents(sub_soups)

    for soup_object in sub_soups.objects:
        object_name = soup_object.get('name')
        print('\n=== Current Object: ' + object_name + " ===")
        consideration = CheckGlobalTimeoutUsedWaits()
        consideration.check_consideration(soup_object)

    full_speed_end = time.clock()
    print('\nFull Process Speed: ' + str(full_speed_end - full_speed_start))


