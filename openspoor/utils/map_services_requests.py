import time
import json
import certifi
import urllib3

from openspoor.utils.singleton import Singleton


class SafeRequest(Singleton):
    def __init__(self):
        self.pool = urllib3.PoolManager(ca_certs=certifi.where())

    def request(self, request_type, url, body):
        return self.pool.request(request_type, url, body=body)

    def get_string(self, request_type, url, body=None):
        if body:
            body = json.dumps(body)
        return self.request(request_type, url, body)._body.decode('UTF-8')

    def get_json(self, request_type, url, body=None):
        return json.loads(self.get_string(request_type, url, body))

    def get_data(self, request_type, url, body):
        if body:
            body = json.dumps(body)
        return json.loads(self.request(request_type, url, body).data)


# def secure_map_services_request(request_type, url, input_json=None, max_retry=5, time_between=1):
#     """
#     Makes call to url and returns obtained data in such a way that if blocked, the request is made again at a later
#     point in time.
#
#     :param url: api call to obtain json
#     :param input_json: dictionary that must be given as json with a post request
#     :param max_retry: maximum number of attempts to retry if request results in an error
#     :param time_between: amount of seconds to wait between requests made if an error occurs on previous attempts
#     :return: dictionary containing json feedback
#     """
#
#     count = 0
#     while count <= max_retry:
#         try:
#             if input_json:
#                 return SafeRequest().get_data('POST', url, input_json)
#             else:
#                 return SafeRequest().get_string('GET', url)
#         except Exception as error:
#             print(error)
#             time.sleep(time_between)
#             count += 1
#             if count >= 1:
#                 raise error
#     raise ConnectionError(f'Unable to connect to {url}')
