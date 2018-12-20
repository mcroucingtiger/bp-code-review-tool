from bs4 import BeautifulSoup
import logging
from SharedCode import ReportPageHelper
from SharedCode.Considerations import ConsiderationsList


def check_obj_has_attach(soup: BeautifulSoup, report_helper: ReportPageHelper):
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
    # TODO fill out this function


    logging.info("'Check System Exception' function called")
    report_helper.set_consideration(ConsiderationsList.CHECK_ACTIONS_USE_ATTACH)

