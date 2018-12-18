from bs4 import BeautifulSoup
import logging
from SharedCode import ReportPageHelper
from SharedCode.Considerations import ConsiderationsList


def check_business_obj_has_attach(soup: BeautifulSoup, report_helper: ReportPageHelper):

    logging.info("'Check System Exception' function called")
    report_helper.set_consideration(ConsiderationsList.CHECK_BUSINESS_OBJ_HAS_ATTACH)

    attach_found = False
    subsheets = soup.find_all('subsheet')  # Find all page names
    for subsheet in subsheets:
        if subsheet.contents[1].string.lower().find("attach") >= 0:  # A page has the work 'Attach' in it
            attach_found = True
    if not attach_found:  # TODO pick up from here (Exception page)
        report_helper.set_error(ConsiderationsList.CHECK_BUSINESS_OBJ_HAS_ATTACH, "Unable to find and an Attach page within the Object"
                                , exception_page)


def check_actions_use_attach(soup: BeautifulSoup, report_helper: ReportPageHelper):
    # TODO fill out this function


    logging.info("'Check System Exception' function called")
    report_helper.set_consideration(ConsiderationsList.CHECK_ACTIONS_USE_ATTACH)

