import json


class ReportHelper:
    """"
    Helper class to categorise all error cases found into a topics (list) > topic (dict) > considerations (list)
    > consideration (dict) > errors (list) > error (dict) structure
    and output a JSON to be returned to the HTTP Request.

    A class so each HTTP request instantiates it's own helper object, and so captures its own report information.
    """
    def __init__(self):
        self.topics = []

    # TODO create a more pythonic implementation
    def set_error(self, topic_name, consideration_name, error_name, error_location):
        """Adds the error to the relevant topic and consideration"""
        error = {'Error': error_name, 'Error Location': error_location}
        for topic in self.topics:
            if topic['Topic Name'] == topic_name:  # Checks the topics list for a dict containing topic name
                for consideration in topic['Considerations']:
                    if consideration["Consideration Name"] == consideration_name:  # Checking consideration list
                        consideration['Errors'].append(error)
                        break
                break

    def set_consideration(self, topic_name, consideration_name):
        """Creates a consideration dict containing an errors list and appends it to its topic's consideration list"""
        consideration = {"Consideration Name": consideration_name, "Errors": []}
        for topic in self.topics:
            if topic['Topic Name'] == topic_name:
                topic['Considerations'].append(consideration)

    def set_topic(self, topic_name):
        """Creates a topic if the given topic does not already exist"""
        new_topic = True
        for topic in self.topics:
            if topic["Topic Name"] == topic_name:
                new_topic = False
                break

        if new_topic:
            add_topic = {"Topic Name": topic_name, "Considerations": []}
            self.topics.append(add_topic)

    def get_report_json(self):
        return json.dumps(self.topics)
