from abc import ABC, abstractmethod
from ..ReportPage import Result
from bs4 import BeautifulSoup


class Consideration(ABC):
    """Abstract class used as the parent to instantiate all consideration classes."""
    CONSIDERATION_NAME = "Override - Title from Report"

    PASS_HURDLE = 0
    FREQUENTLY_HURDLE = 0
    INFREQUENTLY_HURDLE = 0
    """Default values will fail if any errors found."""

    INFREQUENTLY_SCALE = 0.3
    FREQUENTLY_SCALE = 0.7

    def __init__(self, max_score=10):
        self.score = max_score
        self.max_score = max_score  # Default for all Considerations
        self.result = Result.YES
        self.result_forced = False
        self.errors_list = []
        self.warning_list = []

    @abstractmethod
    def check_consideration(self, soup: BeautifulSoup, metadata):
        """Check for error cases within the given soup for each specific report consideration.

        All errors found are appended to the object's self.errors list, with each error being a dict.
        """
        ...

    def evaluate_score_and_result(self, forced_score_scale=None, forced_result=None):
        """Calculate or set the consideration's score and result.

        If no forced values are given, the default if any error exists is a hard fail {score: 0, result: No}.
        """
        # Both forced results are given from config
        if forced_score_scale and forced_result:
            self.score = self.max_score * forced_score_scale
            self.result = forced_result

        # If no forced result is given from the Config file
        # and no forced result is given from within the Consideration check
        else:
            if not self.result_forced:
                if self.errors_list:
                    amount_errors = len(self.errors_list)
                    if amount_errors > self.INFREQUENTLY_HURDLE:
                        self.score = 0
                        self.result = Result.NO

                    elif self.FREQUENTLY_HURDLE < amount_errors <= self.INFREQUENTLY_HURDLE:
                        self.score = self.max_score * self.INFREQUENTLY_SCALE
                        self.result = Result.INFREQUENTLY

                    elif self.PASS_HURDLE < amount_errors <= self.FREQUENTLY_HURDLE:
                        self.score = self.max_score * self.FREQUENTLY_SCALE
                        self.result = Result.FREQUENTLY

                    elif amount_errors <= self.PASS_HURDLE:
                        self.score = self.max_score
                        self.result = Result.YES

                # No Errors
                else:
                    self.score = self.max_score
                    self.result = Result.YES

    def add_to_report(self, report_helper):
        """Add the consideration and its errors' within the the report_helper's considerations list.

        This method should not need to be overridden.
        """
        report_helper.set_consideration(self.CONSIDERATION_NAME, self.max_score, self.score, self.result,
                                        self.errors_list, self.warning_list)

    def _consideration_not_applicable(self):
        self._force_result(Result.NOT_APPLICABLE, 0, 0)

    def _force_result(self, result, score, max_score=None):
        """Set the result of the consideration and override scoring of errors."""
        self.result_forced = True
        self.result = result
        self.score = score
        if max_score is not None:
            self.max_score = max_score
