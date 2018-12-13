import logging
from bs4 import BeautifulSoup
from SharedCode.ReportHelper import *


def check_system_exceptions():
    error_list = []
    logging.info("'Check System Exception' function called")
    # Loading and parsing XML locally (D.A.T)
    infile = open("BPA Object - Kwik Surverys - General.xml", "r")
    contents = infile.read()
    soup = BeautifulSoup(contents, 'lxml')

    # Finding the 'exception stage name' and 'page name' for all exception stages with empty an exception detail field
    exception_stages = soup.find_all('exception')

    for exception_stage in exception_stages:
        if not exception_stage.get('detail') and not exception_stage.get('usecurrent'):
            exception_name = exception_stage.parent.get('name')
            parent_subsheet_id = exception_stage.parent.subsheetid.string
            exception_page = soup.find('subsheet', {'subsheetid': parent_subsheet_id}).contents[1].string

            error = {
                "Exception name": exception_name,
                "Exception page": exception_page
            }
            error_list.append(error)

    # Printing error statement to the console (temporary)

    jsonfile = json.dumps(error_list)
    print(jsonfile)
    for error in error_list:
        print("Exception stage '%s' on page '%s' is missing an Exception Detail."
                     % (error["Exception name"], error["Exception page"]))


def tester_json2():
    rh = ReportHelper()
    topic = "Exception Handling"
    consideration = "Exception Message not exist"''
    rh.set_topic(topic)
    rh.set_consideration(topic, consideration)

    topic = "Naming Convention"
    rh.set_topic(topic)

    consideration = "Stage starts with verb"
    rh.set_consideration(topic, consideration)
    rh.set_error(topic, consideration, "error 1", "Main Page")
    rh.set_error(topic, consideration, "error 2", "Sub Page")

    consideration = "No Infinite Loops"
    rh.set_consideration(topic, consideration)
    rh.set_error(topic, consideration, "error 1", "Main page")
    rh.set_error(topic, consideration, "error 2", "Sub page")

    topic = "Object Stuff"
    rh.set_topic(topic)

    consideration = "Stage starts with verb"
    rh.set_consideration(topic, consideration)
    rh.set_error(topic, consideration, "error 1", "Main Page")
    rh.set_error(topic, consideration, "error 2", "Sub Page")

    consideration = "No Infinite Loops"
    rh.set_consideration(topic, consideration)
    rh.set_error(topic, consideration, "error 1", "Main Page")
    rh.set_error(topic, consideration, "error 2", "Sub Page")

    output_json = rh.get_report_json()
    print(output_json)


tester_json2()


