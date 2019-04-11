import typing
import azure.functions as func
from unittest import TestCase

from ... import CodeReview

class TestMain(TestCase):

    def setUp(self):
        self.req = func.HttpRequest(
                method='GET',
                body=None,
                url='/my_function',
                params={'name': 'Test'}
        )

    def test_main_fail(self):
        self.assertRaises(ValueError, CodeReview.main(self.request))


