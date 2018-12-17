from bs4 import BeautifulSoup
import logging
from ReportPageHelper import ReportPageHelper


def check_business_obj_has_attach(soup: BeautifulSoup, report_helper: ReportPageHelper):
    CONSIDERATION_NAME = "Does the Business Object have an 'Attach' Action that reads " \
                         "the connected status before Attaching?"

    logging.info("'Check System Exception' function called")
    report_helper.set_consideration(CONSIDERATION_NAME)

    attach_found = False
    subsheets = soup.find_all('subsheet')  # Find all page names
    for subsheet in subsheets:
        if subsheet.contents[1].string.lower().find("attach") >= 0:  # A page has the work 'Attach' in it
            attach_found = True

    if attach_found == False:  #TODO pick up from here (Exception page)
        report_helper.set_error(CONSIDERATION_NAME, "Unable to find and an Attach page within the Object"
                                , exception_page)

def check_actions_use_attach(soup: BeautifulSoup, report_helper: ReportPageHelper):
    CONSIDERATION_NAME = "Do all Actions use the Attach action?"

    logging.info("'Check System Exception' function called")
    report_helper.set_consideration(CONSIDERATION_NAME)

