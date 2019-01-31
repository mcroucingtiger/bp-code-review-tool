from bs4 import SoupStrainer, BeautifulSoup
import time
from collections import namedtuple
from ..CodeReview import make_all_soups,Sub_Soup, get_local_xml
from multiprocessing import Pool, Queue, Process
import math

print("Local unit testing page started")

_release_path = "C:/Users/MorganCrouch/Documents/Github/CodeReviewSAMProj/Test Releases/Multi-Object_Process.bprelease"
release_path = "C:/Users/MorganCrouch/Documents/Reveal Group/Auto Code Review/" \
               "Test Releases Good/MI Premium Payments - Backup Release v2.0.bprelease"
_release_path = "C:/Users/MorganCrouch/Documents/Reveal Group/Auto Code Review/" \
               "Test Releases Good/LAMP - Send Correspondence_V01.01.01_20181214.bprelease"


def has_attr_bpversion(tag):
    """Only Objects have an attribute called bpversion. This filter function should return all the Object tags"""
    return tag.has_attr('bpversion')


def get_local_xml_soups() -> BeautifulSoup:
    """Gets and converts local XML into Beautiful Soup objects"""
    contents = get_local_xml(release_path)
    start = time.clock()
    global xml_string
    xml_string = contents
    mp_factorizer(["header"], 4)
    # sub_soups = make_soups(contents)
    end = time.clock()
    print("making all sub_soups " + str(end - start))

    print('\nObjects:')
    for object_tag in sub_soups.objects:
        print(object_tag.get('name'))
    print('\nProcesses:')
    for process_tag in sub_soups.processes:
        print(process_tag.get('name'))
    print('\nQueue:')
    for queue_tag in sub_soups.queues:
        print(queue_tag.get('name'))

    return sub_soups


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
        subsheets = soup.find_all('subsheet', recursive=False)  # TODO this can turn off recursive?
        for subsheet in subsheets:
            action_name = subsheet.next_element.string.lower()
            # Check the Action does not contain a word from the blacklist
            if not any(blacklist_action in action_name for blacklist_action in blacklist_attach_actions):
                print("Not blacklisted - " + subsheet.next_element.string )
                if not _action_begins_attach(subsheet, soup):
                    print("/// Action failed ///")
                    #print("Action doesn't begin with an attach")

                    ...  # Add error to the report page helper
                else:
                    print("*******************")
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


def get_single_soup(strainer_param):
    individual_soup = None
    if strainer_param == 'header':
      soup_strainer = SoupStrainer(strainer_param)
      individual_soup = BeautifulSoup(xml_string, 'lxml', parse_only=soup_strainer)

    # elif strainer_param == 'process' or strainer_param == 'work-queue':
    #     soup_strainer = SoupStrainer(strainer_param, xmlns=True)
    #     individual_soup = BeautifulSoup(xml_string, 'lxml', parse_only=soup_strainer)

    return individual_soup


def mp_factorizer(elements, nprocs):

    def worker(elements, out_q):
        """ The worker function, invoked in a process. 'nums' is a
            list of numbers to factor. The results are placed in
            a dictionary that's pushed to a queue.
        """
        outdict = {}
        for element in elements:
            outdict[element] = get_single_soup(element)
        out_q.put(outdict)

    # Each process will get 'chunksize' nums and a queue to put his out
    # dict into
    out_q = Queue()
    chunksize = int(math.ceil(len(elements) / float(nprocs)))
    procs = []

    for i in range(nprocs):
        p = Process(
                target=worker,
                args=(elements[chunksize * i:chunksize * (i + 1)],
                      out_q))
        procs.append(p)
        p.start()

    # Collect all results into a single result dict. We know how many dicts
    # with results to expect.
    resultdict = {}
    for i in range(nprocs):
        resultdict.update(out_q.get())

    # Wait for all worker processes to finish
    for p in procs:
        p.join()

    return resultdict



if __name__ == '__main__':
    print('__main__ running for UnitTesting')
    full_speed_start = time.clock()
    sub_group = get_local_xml_soups()
    for soup_object in sub_group.objects:
        object_name = soup_object.next_element.get('name')
        print('\n=== Current Object: ' + object_name + " ===")
        check_consideration(soup_object)
    full_speed_end = time.clock()
    print('\nFull Process Speed: ' + str(full_speed_end - full_speed_start))


