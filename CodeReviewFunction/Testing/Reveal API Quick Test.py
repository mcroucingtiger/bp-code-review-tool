"""
Testing the Capture API with Python.
"""
import requests

# This will definitely change. 401 response indicates Zaid needs to be asked for a new token
auth_token = 'eyJhbGciOiJIUzI1NiJ9.eyJleHAiOjE1NTYyOTQ0MDAsInN1YiI6IkpMTCBUZXN0IFVzZXIiLCJzY2hlbWEiOiJkZW1vIiwiZGF0YS' \
             'I6Im95UXl6WGg3WUREOGZnWUc0WUEiLCJpc3MiOiJyZXZlYWx0b29scy5jb20iLCJqdGkiOiJweGVHYWxpR1NQRlBkTFNrUU9zUGp3' \
             'IiwiaWF0IjoxNTU2MjA4MDA1LCJuYmYiOjE1NTYyMDc4ODUsImF1ZCI6ImNhcHR1cmUifQ.a8q5VG6IyDTuD5l-aku6VkTxqYviE3' \
             'JQYqOkP6X1QWc'

base_url = 'https://capture.revealtools.com'
application = '/demo/applications/oyQyzXh7YDD8fgYG4YA'
headers = {'Authorization': 'Bearer' + auth_token, 'Accept': 'application/hal+json'}
r = requests.get(base_url + application, headers=headers)
print('Status Code: ' + str(r.status_code))
response_json = r.json()

for activity in response_json['activities']:
    method = ''
    content_type = ''
    href = ''

    print(activity['name'])
    if activity['name'] == 'Daily Team Huddles':  # 'Activity' in Capture relates to a Consideration
        method = activity['_links']['self']['method']
        content_type = activity['_links']['self']['type']
        href = activity['_links']['self']['href']

        # Method should always be POST
        if method == 'POST':
            headers = {'Authorization': 'Bearer' + auth_token, 'Content-Type': content_type}
            # Note the value needs to be an int. This will be its relative score out of 100
            body = {'value': 1, 'context': 'Jpel'}
            response = requests.post(base_url + href, body, headers=headers)
            print('Post response status code: ' + str(response.status_code))
            break





