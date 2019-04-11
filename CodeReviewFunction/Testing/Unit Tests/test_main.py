import typing
import azure.functions as func
from unittest import TestCase

from ... import CodeReview

class TestMain(TestCase):

    # Supposedly you can create a dummy func.HttpRequest after a update in Jan, but i can't get it to work
    # https://github.com/Azure/azure-functions-python-worker/wiki/Unit-Testing-Guide
    #

    def setUp(self):
        self.req = func.HttpRequest(
                method='GET',
                body=None,
                url='/my_function',
                params={'name': 'Test'}
        )

    def test_main_fail(self):
        self.assertRaises(ValueError, CodeReview.main(self.request))


