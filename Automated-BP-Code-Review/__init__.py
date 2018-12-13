import logging
import azure.functions as func
from bs4 import BeautifulSoup
import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'SharedCode')))

from SharedCode import ExceptionHandling, ReportHelper
import SharedCode
# import SharedCode.ReportHelper as ReportHelper
# from SharedCode.ExceptionHandling import *

print(__file__)
print(os.path.join(os.path.dirname(__file__), '..'))
print(os.path.dirname(os.path.realpath(__file__)))
print(os.path.abspath(os.path.dirname(__file__)))

# from .SharedCode.ReportHelper import *
# from SharedCode import ReportHelper

# logging.critical .error .warning .info .debug
logging.info("Init page finished")


def main(req: func.HttpRequest) -> func.HttpResponse:
    xml_string = ''
    report_helper = ReportHelper()

    logging.info('Python HTTP trigger function processed a request.')
    try:
        req_body = req.get_body()
        xml_string = req_body
    except ValueError:
        logging.error("Unable to access request body")
        pass

    if xml_string:
        error_cases = process_topics(report_helper, xml_string)
        return func.HttpResponse(json.dumps(error_cases))
    else:
        return func.HttpResponse(
            "Unable to read XML",
            status_code=400
        )

    return func.HttpResponse("Managed to get a python script working as an azure funciton. Now just have to build the thing")


def process_topics(report_helper, xml_string):
    soup = BeautifulSoup(xml_string, 'lxml')
    error_cases = check_exception_details(soup, report_helper)
    return error_cases



