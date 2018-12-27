import logging
from bs4 import BeautifulSoup  # Note that lxml has a external c depedency
from SharedCode.ReportPageHelper import ReportPageHelper, error_as_dict
from SharedCode.Considerations import ConsiderationsList


def check_exception_details(soup: BeautifulSoup):
    """Check to ensure all Exception stages do not contain blank exception details"""
    errors = []
    logging.info("'Check Exception Detail function called")

    # Finding the 'exception stage name' and 'page name' for all exception stages with empty an exception detail field
    exception_stages = soup.find_all('exception')
    for exception_stage in exception_stages:
        if not exception_stage.get('detail') and not exception_stage.get('usecurrent'):  # No detail and not preserve
            exception_name = exception_stage.parent.get('name')
            parent_subsheet_id = exception_stage.parent.subsheetid.string
            exception_page = soup.find('subsheet', {'subsheetid': parent_subsheet_id}).next_element.string

            errors.append(error_as_dict(exception_name, exception_page))

    return errors
