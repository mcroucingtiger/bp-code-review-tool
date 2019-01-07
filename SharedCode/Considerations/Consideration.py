from abc import ABC, abstractmethod
from SharedCode.ReportPageHelper import Result, Impact
from bs4 import BeautifulSoup


class Consideration(ABC):
    """Abstract class used as the parent for all consideration classes."""
    def __init__(self, consideration_name):
        self.max_score = 10
        self.score = 10
        self.name = consideration_name
        self.result = Result.YES
        self.impact = Impact.None_
        self.errors = []

    @abstractmethod
    def check_consideration(self, soup: BeautifulSoup) -> list:
        """Check for error cases within the given soup for each specific report consideration.

        All errors found are appended to the object's self.errors list, with each error being a dict."""
        ...

    @abstractmethod
    def evaluate_score_and_result(self):
        """Calculate the consideration's score and result. Default value is hard fail {score: 0, result: No}."""
        if self.errors:
            self.score = 0
            self.result = Result.NO

    @abstractmethod
    def add_to_report(self, report_helper):
        """Add the consideration and its errors' within the the report_helper's considerations list."""
        report_helper.set_consideration(self.name, self.max_score, self.score, self.result)
        for error in self.errors:
            report_helper.set_error(self.name, error)
