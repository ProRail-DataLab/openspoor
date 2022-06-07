import time
import json
import certifi
import urllib3

from openspoor.utils.singleton import Singleton


class SafeRequest(Singleton):
    def __init__(self):
        self.pool = urllib3.PoolManager(ca_certs=certifi.where())

    def get_response(self, request_type, url, headers=None):
        if headers:
            headers = json.dumps(headers)
        return self.pool.request(request_type, url,headers=headers)._body.decode('UTF-8')

    def get_out_json(self, url, input_json=None):
        return json.loads(self.get_response('GET', url, input_json))

    def get_json(self, request_type, url, input_json):
        return json.loads(self.pool.request(request_type, url, body=json.dumps(input_json)).data)


def secure_map_services_request(request_type, url, input_json=None, max_retry=5, time_between=1):
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
                print("DOING THIS")
                return SafeRequest().get_json('POST', url, input_json)
                # pool = SafeRequest().pool
                # print(pool)
                # request = SafeRequest().pool.request("POST", url, headers=json)
                # print(request)
                # data = request.data
                # print(data)
                # return json.loads(SafeRequest().pool.request("POST", url, fields=json).data)
            else:
                print("DOING THAT")
                return SafeRequest().get_response('GET', url)
            # return json.loads(response.data)
        except Exception as error:
            print(error)
            time.sleep(time_between)
            count += 1
            if count >= 1:
                raise error
    raise ConnectionError(f'Unable to connect to {url}')
