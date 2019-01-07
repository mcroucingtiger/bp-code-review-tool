import logging
from bs4 import BeautifulSoup  # Note that lxml has a external c depedency
from SharedCode.ReportPageHelper import ReportPageHelper, error_as_dict, Result
from SharedCode.Considerations.Consideration import Consideration


class CheckExceptionDetails(Consideration):
    def __init__(self):
        CONSIDERATION_NAME = "Do all Exception stages have an exception detail?"
        super().__init__(CONSIDERATION_NAME)

    def check_consideration(self, soup: BeautifulSoup) -> list:
        logging.info("'CheckExceptionDetail method called")

        # Finding the 'exception stage name' and 'page name' for all exception stages
        # with empty an exception detail field
        exception_stages = soup.find_all('exception')
        for exception_stage in exception_stages:
            if not exception_stage.get('detail') and not exception_stage.get(
                    'usecurrent'):  # No detail and not preserve
                exception_name = exception_stage.parent.get('name')
                parent_subsheet_id = exception_stage.parent.subsheetid.string
                exception_page = soup.find('subsheet', {'subsheetid': parent_subsheet_id}).next_element.string

                self.errors.append(error_as_dict(exception_name, exception_page))

    def evaluate_score_and_result(self):
        """Calculate the consideration's score and result. Default value is hard fail {score: 0, result: No}."""
        if self.errors:
            if len(self.errors) < 2:
                self.score = self.max_score * 0.7
                self.result = Result.FREQUENTLY
            elif 2 <= len(self.errors) <= 4:
                self.score = self.max_score * 0.3
                self.result = Result.INFREQUENTLY
            else:
                self.score = 0
                self.result = Result.NO

    def add_to_report(self, report_helper):
        super().add_to_report(report_helper)


