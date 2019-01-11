from abc import ABC, abstractmethod
from ..ReportPage import Result
from bs4 import BeautifulSoup


class Consideration(ABC):
    """Abstract class used as the parent for all consideration classes."""
    CONSIDERATION_NAME = "Override - Title from Report"

    def __init__(self, consideration_name, max_score=10):
        self.max_score = max_score
        self.score = max_score
        self.name = consideration_name
        self.result = Result.YES
        self.errors = []

    @abstractmethod
    def check_consideration(self, soup: BeautifulSoup) -> list:
        """Check for error cases within the given soup for each specific report consideration.

        All errors found are appended to the object's self.errors list, with each error being a dict.
        """
        ...

    def evaluate_score_and_result(self, forced_score_scale=None, forced_result=None):
        """Calculate or set the consideration's score and result.

        If no forced values are given, the default if any error exists is a hard fail {score: 0, result: No}.
        """
        # If no forced result is given from the Config file
        if not forced_score_scale and not forced_result:
            if self.errors:
                self.score = 0
                self.result = Result.NO
            else:
                self.score = self.max_score
                self.result = Result.YES
        else:
            self.score = self.max_score * forced_score_scale
            self.result = forced_result

    def add_to_report(self, report_helper):
        """Add the consideration and its errors' within the the report_helper's considerations list."""
        report_helper.set_consideration(self.name, self.max_score, self.score, self.result)
        for error in self.errors:
            report_helper.set_error(self.name, error)
