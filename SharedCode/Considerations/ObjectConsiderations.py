from bs4 import BeautifulSoup
import logging
from SharedCode.ReportPageHelper import ReportPageHelper
from SharedCode.Considerations.ConsiderationsList import *
from SharedCode.ReportPageHelper import error_as_dict
from SharedCode.Considerations.Consideration import Consideration


class CheckObjHasAttach(Consideration):
    def __init__(self):
        super().__init__()
        self.value = "Does the Business Object have an 'Attach' Action " \
                     "that reads the connected status before Attaching?"

    def check_consideration(self, soup: BeautifulSoup) -> list:
        logging.info("check_obj_has_attach function called")
        attach_found = False
        subsheets = soup.find_all('subsheet')  # Find all page names
        for subsheet in subsheets:
            if subsheet.next_element.string.lower().find("attach") >= 0:  # A page has the work 'Attach' in it
                attach_found = True
                break

        if not attach_found:
            self.errors.append(error_as_dict("Unable to find and an Attach page within the Object", "N/A"))

    # TODO: determine if this is needed or if you can make the method not abstract.
    def evaluate_consideration(self):
        super().evaluate_consideration()

    def add_consideration(self, report_helper):
        super().add_consideration(report_helper)





def check_actions_use_attach(soup: BeautifulSoup, report_helper: ReportPageHelper):
    # TODO fill out this function


    logging.info("'Check System Exception' function called")
    report_helper.set_consideration(CHECK_ACTIONS_USE_ATTACH)

