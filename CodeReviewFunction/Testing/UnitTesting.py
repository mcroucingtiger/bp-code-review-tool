from bs4 import BeautifulSoup
import time
from ..CodeReview import get_local_xml
from CodeReviewFunction.SoupUtilities import extract_pickled_soups
from CodeReviewFunction.CodeReview import deserialize_to_soup
from .. import SoupUtilities
import pickle
from ..Considerations.ObjectConsiderations import *
from ..Considerations.ProcessConsiderations import *


# Main
release_path_ = "C:/Users/MorganCrouch/Documents/Github/CodeReviewSAMProj/CodeReviewFunction" \
               "/Testing/SAM Processed XML/LAMP.xml"
release_path_ = "C:/Users/MorganCrouch/Documents/Github/CodeReviewSAMProj/CodeReviewFunction" \
                "/Testing/SAM Processed XML/MERS.xml"
release_path = "C:/Users/MorganCrouch/Documents/Github/CodeReviewSAMProj/CodeReviewFunction" \
                "/Testing/SAM Processed XML/MI Report.xml"
release_path_ = "C:/Users/MorganCrouch/Documents/Github/CodeReviewSAMProj/CodeReviewFunction" \
                "/Testing/SAM Processed XML/Multi-Process.xml"
# Additional
release_path_ = "C:/Users/MorganCrouch/Desktop/Bunnings Cloud Storage.bprelease"  # Really shitty object
release_path_ = "C:/Users/MorganCrouch/Desktop/SDO 20190111.bprelease"
release_path_ = "C:/Users/MorganCrouch/Desktop/zTemplateBackupExport.bprelease"
release_path_ = "C:/Users/MorganCrouch/Desktop/Orora Backup 20180328.bprelease"
release_path_ = "C:/Users/MorganCrouch/Desktop/BTS-IBMSynergyBillingDataUpdate-Release-V2.1.bprelease"

# Dummy
release_path_ = "C:/Users/MorganCrouch/Desktop/Testing Release.bprelease"
release_path_ = "C:/Users/MorganCrouch/Desktop/test.bprelease"
release_path_ = "C:/Users/MorganCrouch/Desktop/Another Delete.xml"

# Pickled Tests
pickled_path_ = "C:/Users/MorganCrouch/Documents/Github/CodeReviewSAMProj/CodeReviewFunction" \
                "/Testing/Fixtures/LAMP_pickled_soups.txt"
pickled_path_ = "C:/Users/MorganCrouch/Documents/Github/CodeReviewSAMProj/CodeReviewFunction" \
                "/Testing/Fixtures/MERS_pickled_soup.txt"
pickled_path_ = "C:/Users/MorganCrouch/Documents/Github/CodeReviewSAMProj/CodeReviewFunction" \
                "/Testing/Fixtures/MI_Premium_pickled_soups.txt"
pickled_path_ = "C:/Users/MorganCrouch/Documents/Github/CodeReviewSAMProj/CodeReviewFunction" \
                "/Testing/Fixtures/multi_process_pickled_soups.txt"
pickled_path_ = "C:/Users/MorganCrouch/Documents/Github/CodeReviewSAMProj/CodeReviewFunction" \
                "/Testing/Fixtures/SDO_pickled_soups.txt"


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


def get_local_pickled_results(file_location):
    """Get results list from the pickled version saved in file"""
    with open(file_location, 'rb') as file:
        results = pickle.load(file)
    return results


if __name__ == '__main__':
    print('__main__ running for UnitTesting')
    full_speed_start = time.clock()
    # --- To Use Raw XML ---
    sub_soups = deserialize_to_soup(extract_pickled_soups(get_local_xml(release_path)))
    # -- To Use Pre-Pickled ---
    # pickled_results = get_local_pickled_results(pickled_path)
    # sub_soups = deserialize_to_soup(pickled_results)

    print_sub_soups_contents(sub_soups)

    consid_start = time.clock()
    for soup_object in sub_soups.objects:
        metadata = {}
        object_name = soup_object.get('name')
        object_type, estimated = SoupUtilities.determine_object_type(object_name.lower(), soup_object)
        metadata['object type'] = object_type

        a = {'Delivery Stage': ''}
        metadata['additional info'] = a
        metadata['additional info']['Delivery Stage'] = 'Production'

        print('\n=== Current Object: {} ({}) ==='.format(object_name, object_type))

        consideration = CheckTechnologySpecificAttributes()
        consideration.check_consideration(soup_object, metadata)
    consid_end = time.clock()

    print("\nConsideration Time: " + str(consid_end - consid_start))

    full_speed_end = time.clock()
    print('\nFull Process Speed: ' + str(full_speed_end - full_speed_start))


