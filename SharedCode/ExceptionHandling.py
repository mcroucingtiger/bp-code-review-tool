import logging
from bs4 import BeautifulSoup  # Note that lxml has a external c depedency
from ReportPageHelper import ReportPageHelper

TOPIC_NAME = 'Exception Handling'


def check_exception_details(soup: BeautifulSoup, report_helper: ReportPageHelper):
    """Check to ensure all Exception stages do not contain blank exception details"""
    CONSIDERATION_NAME = "Do all Exception stages have an exception detail? "

    logging.info("'Check System Exception' function called")
    report_helper.set_topic(TOPIC_NAME)
    report_helper.set_consideration(TOPIC_NAME, CONSIDERATION_NAME)

    # Finding the 'exception stage name' and 'page name' for all exception stages with empty an exception detail field
    exception_stages = soup.find_all('exception')
    for exception_stage in exception_stages:
        if not exception_stage.get('detail') and not exception_stage.get('usecurrent'):  # No detail and not preserve
            exception_name = exception_stage.parent.get('name')
            parent_subsheet_id = exception_stage.parent.subsheetid.string
            exception_page = soup.find('subsheet', {'subsheetid': parent_subsheet_id}).contents[1].string

            # Append the error to the report list
            report_helper.set_error(TOPIC_NAME, CONSIDERATION_NAME, exception_name, exception_page)
