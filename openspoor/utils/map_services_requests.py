import requests
import time
import json


def secure_map_services_request(url, input_json=None, max_retry=5, time_between=1):
    """
    Makes call to url and returns obtained data in such a way that if blocked, the request is made again at a later
    point in time.

    :param url: api call to obtain json
    :param input_json: dictionary that must be given as json with a post request
    :param max_retry: maximum number of attempts to retry if request results in an error
    :param time_between: amount of seconds to wait between requests made if an error occurs on previous attempts
    :return: dictionary containing json feedback
    """
    count = 0
    while count <= max_retry:
        try:
            if input_json:
                response = requests.post(url, json=input_json)
            else:
                response = requests.get(url, verify=False)
            return json.loads(response.content)
        except Exception as error:
            time.sleep(time_between)
            count += 1
            if count >= max_retry:
                raise error
    raise requests.exceptions.ConnectionError('Unable to connect to ' + url)
