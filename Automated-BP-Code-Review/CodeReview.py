import logging
import azure.functions as func
from bs4 import BeautifulSoup
from bs4 import SoupStrainer
import json
import sys
from os import path
from collections import namedtuple
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from SharedCode.ReportPageHelper import ReportPageHelper, Result
from SharedCode.Considerations.GeneralConsiderations import check_exception_details
from SharedCode.Considerations.ObjectConsiderations import check_obj_has_attach
from SharedCode.Considerations.ConsiderationsList import *


# logging.critical .error .warning .info .debug
logging.info("__init__ page running")
Sub_Soup = namedtuple('Sub_Soup', 'processes, objects, queues')


def main():#req: func.HttpRequest) -> func.HttpResponse:
    print("Main running")
    xml_string = ''
    report_pages = []
    logging.info("Python HTTP trigger function processed a request.")

    # try:
    #     req_body = req.get_body()
    #     xml_string = req_body
    # except ValueError:
    #     logging.error("Unable to access request body")
    #     pass

    # Testing only
    release_path = "C:/Users/MorganCrouch/Desktop/testing Release.bprelease"
    infile = open(release_path, "r")
    xml_string = infile.read()

    if xml_string:  # If the XML was able to be extracted from HTTP, it gets parsed into a BeautifulSoup Obj
        sub_soups = make_soups(xml_string)

        for process_tag in sub_soups.processes.contents:
            report_page_dict = make_report_process(process_tag)
            report_pages.append(report_page_dict)

        for object_tag in sub_soups.objects.contents:
            report_page_dict = make_report_object(object_tag)
            report_pages.append(report_page_dict)

        json_report = json.dumps(report_pages)
        print(json_report)

        return func.HttpResponse(json_report)

    else:
        return func.HttpResponse(
            "Unable to read XML",
            status_code=400
        )


def make_soups(xml_string) -> Sub_Soup:
    """Turns the xml into a named tuple of BeautifulSoup objects for all processes, objects and queues"""
    # Look at Local testing script to see how access names
    only_objects = SoupStrainer('object', xmlns=True)
    soup_objects = BeautifulSoup(xml_string, 'lxml', parse_only=only_objects)

    only_processes = SoupStrainer('process', xmlns=True)
    soup_processes = BeautifulSoup(xml_string, 'lxml', parse_only=only_processes)

    only_work_queue = SoupStrainer('work-queue', xmlns=True)
    soup_queue = BeautifulSoup(xml_string, 'lxml', parse_only=only_work_queue)

    return Sub_Soup(soup_processes, soup_objects, soup_queue)


def make_report_process(process_soup):
    """Use the filtered soup of a single process tag element to generate the JSON for a page in the report."""
    report_helper = ReportPageHelper()
    report_helper.set_page_type('Process', process_soup)
    logging.info("Running make_report_process function for " + report_helper.page_name)

    # TODO: fill out process side

    return report_helper.get_report_page()


def make_report_object(object_soup):
    """Use the filtered soup of a single object tag element to generate the JSON for a page in the report."""
    report_helper = ReportPageHelper()
    report_helper.set_page_type('Object', object_soup)
    logging.info("Running make_report_object function for " + report_helper.page_name)

    # All modules intended for creating a object specific page in the report.
    # If statements are for the scoring of individual modules that any errors.

    errors = check_exception_details(object_soup)
    set_consideration_and_errors(report_helper, CHECK_EXCEPTION_DETAILS, errors)
    if errors:
        report_helper.set_consideration_score(CHECK_EXCEPTION_DETAILS.value, score=0, result=Result.NO)

    errors = check_obj_has_attach(object_soup)
    set_consideration_and_errors(report_helper, CHECK_OBJ_HAS_ATTACH, errors)
    if errors:
        report_helper.set_consideration_score(CHECK_OBJ_HAS_ATTACH.value, score=0, result=Result.NO)

    return report_helper.get_report_page()


def set_consideration_and_errors(report_helper, consideration_tuple, errors):
    """Sets the consideration and its errors within the the report_helper's considerations list"""
    report_helper.set_consideration(consideration_tuple.value, consideration_tuple.max_score)
    for error in errors:
        report_helper.set_error(CHECK_OBJ_HAS_ATTACH.value, error)


main()
