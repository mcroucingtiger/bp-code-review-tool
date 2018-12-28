from bs4 import BeautifulSoup
import logging
from SharedCode.ReportPageHelper import ReportPageHelper
from SharedCode.Considerations.ConsiderationsList import *
from SharedCode.ReportPageHelper import error_as_dict
"""Functions to find the errors for the considerations in the Object Report page.

All functions should take in a soup and return a list of error objects
 """


def check_obj_has_attach(soup: BeautifulSoup) -> list:
    logging.info("check_obj_has_attach function called")
    errors = []
    attach_found = False
    subsheets = soup.find_all('subsheet')  # Find all page names
    for subsheet in subsheets:
        if subsheet.next_element.string.lower().find("attach") >= 0:  # A page has the work 'Attach' in it
            attach_found = True
            break

    if not attach_found:
        errors.append(error_as_dict("Unable to find and an Attach page within the Object", "N/A"))

    return errors


def check_actions_use_attach(soup: BeautifulSoup, report_helper: ReportPageHelper):
    # TODO fill out this function


    logging.info("'Check System Exception' function called")
    report_helper.set_consideration(CHECK_ACTIONS_USE_ATTACH)

