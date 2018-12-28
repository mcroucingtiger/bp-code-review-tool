from abc import ABC, abstractmethod
from SharedCode.ReportPageHelper import Result, Impact
from bs4 import BeautifulSoup


class Consideration(ABC):
    def __init__(self):
        self.max_score = 10
        self.score = 10
        self.value = ""
        self.result = Result.YES
        self.impact = Impact.None_
        self.errors = []
        super().__init__()

    @abstractmethod
    def check_consideration(self, soup: BeautifulSoup) -> list:
        ...

    @abstractmethod
    def evaluate_consideration(self):
        """Calculate the consideration's score and result. Default value is hard fail {score: 0, result: No}."""
        if self.errors:
            self.score = 0
            self.result = Result.NO

    @abstractmethod
    def add_consideration(self, report_helper):
        """Add the consideration and its errors' within the the report_helper's considerations list."""
        report_helper.set_consideration(self.value, self.max_score)
        for error in self.errors:
            report_helper.set_error(self.value, error)
