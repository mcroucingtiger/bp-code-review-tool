from bs4 import BeautifulSoup
import time
from ..CodeReview import extract_pickled_soups, get_local_xml, deserialize_to_soup
import pickle

print("Local unit testing page started")

_release_path = "C:/Users/MorganCrouch/Documents/Github/CodeReviewSAMProj/Test Releases/Multi-Object_Process.bprelease"
release_path = "C:/Users/MorganCrouch/Documents/Reveal Group/Auto Code Review/" \
               "Test Releases Good/MI Premium Payments - Backup Release v2.0.bprelease"
_release_path = "C:/Users/MorganCrouch/Documents/Reveal Group/Auto Code Review/" \
               "Test Releases Good/LAMP - Send Correspondence_V01.01.01_20181214.bprelease"


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


def check_consideration(soup: BeautifulSoup) -> list:
    """Check if an Object starts with Attach page."""
    BLACKLIST_ATTACH_ACTIONS = ['launch', 'close', 'terminate', 'attach', 'initialise', 'clean up', 'detach']
    blacklist_object_names = ['wrapper']

    object_name = soup_object.get('name').lower()
    # Current Object name not blacklisted
    # TODO pretty sure its still not ignoring
    if not any(blacklist_word in object_name for blacklist_word in blacklist_object_names):
        # Iterate over all Actions in the Object
        actions = soup.find_all('subsheet')  # Turning off recursion seems to make no speed improvement?
        for action in actions:
            action_name = action.next_element.string.lower()
            # Check the Action does not contain a word from the blacklist
            if not any(blacklist_action in action_name for blacklist_action in BLACKLIST_ATTACH_ACTIONS):
                print("Not blacklisted - " + action.next_element.string)
                if not _action_begins_attach(action, soup):
                    print("/// Action failed ///")
                    #print("Action doesn't begin with an attach")

                    ...  # Add error to the report page helper
                else:
                    print("*******************")
                    pass
            else:
                print(action_name + " -- blackisted action")
    else:
        # Add error that object was blacklisted but force max score and result of Not Applicable
        print(object_name + " -- blacklisted object")


def _action_begins_attach(subsheet, soup):
    """Return True if an Action's page starts with an Attach page stage"""
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


def get_local_pickled_results():
    """Get results list from the pickled version saved in file"""
    file_location = 'C:/Users/MorganCrouch/Documents/Github/CodeReviewSAMProj/CodeReviewFunction' \
                    '/Testing/results_big_testing.txt'
    with open(file_location, 'rb') as file:
        results = pickle.load(file)
    return results


if __name__ == '__main__':
    print('__main__ running for UnitTesting')
    full_speed_start = time.clock()

    # Using functions in CodeReview
    pickled_results = get_local_pickled_results()
    sub_soups = deserialize_to_soup(pickled_results)
    print_sub_soups_contents(sub_soups)

    for soup_object in sub_soups.objects:
        object_name = soup_object.get('name')
        print('\n=== Current Object: ' + object_name + " ===")
        check_consideration(soup_object)

    full_speed_end = time.clock()
    print('\nFull Process Speed: ' + str(full_speed_end - full_speed_start))


