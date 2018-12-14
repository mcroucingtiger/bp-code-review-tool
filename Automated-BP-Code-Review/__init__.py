import logging
import azure.functions as func
from bs4 import BeautifulSoup
from bs4 import SoupStrainer
import sys
import os
from collections import namedtuple
sys.path.append(os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', 'SharedCode')))
from ReportPageHelper import ReportPageHelper
from ExceptionHandling import check_exception_details

# logging.critical .error .warning .info .debug
logging.info("__init__ page running")
Sub_Soup = namedtuple('Sub_Soup', 'processes, objects, queues')


def main(req: func.HttpRequest) -> func.HttpResponse:
    xml_string = ''
    report_pages = []  #TODO Check this actually converts into a JSON
    logging.info("Python HTTP trigger function processed a request.")

    try:
        req_body = req.get_body()
        xml_string = req_body
    except ValueError:
        logging.error("Unable to access request body")
        pass
    if xml_string:  # Happy path :)
        sub_soups = make_soups(xml_string)
        for process_tag in sub_soups.processes.contents:
            report_page = make_report_process(process_tag)
            report_pages.append(report_page)

        for object_tag in sub_soups.objects.contents:
            report_page = make_report_object(object_tag)
            report_pages.append(report_page)

        return func.HttpResponse()#report_helper.get_report_json())

    else:
        return func.HttpResponse(
            "Unable to read XML",
            status_code=400
        )

    return func.HttpResponse("Managed to get a python script working as an azure funciton. Now just have to build the thing")


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
    """Uses the filtered soup of a single process tag element to generate the JSON for a page in the report """
    report_helper = ReportPageHelper()

    # All modules intended for creating a process specific page in the report
    check_exception_details(process_soup, report_helper)
    return report_helper.get_topics_list()


def make_report_object(object_soup):
    """Uses the filtered soup of a single object tag element to generate the JSON for a page in the report """
    report_helper = ReportPageHelper()

    # All modules intended for creating a object specific page in the report
    check_exception_details(object_soup, report_helper)
    return report_helper.get_topics_list()




