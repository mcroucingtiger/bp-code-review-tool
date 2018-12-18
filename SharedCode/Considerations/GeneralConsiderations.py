import logging
from bs4 import BeautifulSoup  # Note that lxml has a external c depedency
from SharedCode import ReportPageHelper
from SharedCode.Considerations import ConsiderationsList


def check_exception_details(soup: BeautifulSoup, report_helper: ReportPageHelper):
    """Check to ensure all Exception stages do not contain blank exception details"""

    logging.info("'Check Exception Detail function called")
    report_helper.set_consideration(ConsiderationsList.CHECK_EXCEPTION_DETAILS)

    # Finding the 'exception stage name' and 'page name' for all exception stages with empty an exception detail field
    exception_stages = soup.find_all('exception')
    for exception_stage in exception_stages:
        if not exception_stage.get('detail') and not exception_stage.get('usecurrent'):  # No detail and not preserve
            exception_name = exception_stage.parent.get('name')
            parent_subsheet_id = exception_stage.parent.subsheetid.string
            exception_page = soup.find('subsheet', {'subsheetid': parent_subsheet_id}).next_element.string

            # Append the error to the report list
            report_helper.set_error(ConsiderationsList.CHECK_EXCEPTION_DETAILS, exception_name, exception_page)
