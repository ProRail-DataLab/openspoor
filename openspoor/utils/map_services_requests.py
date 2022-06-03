import time
import json
import certifi
import urllib3
from functools import lru_cache


@lru_cache
def safe_request():
    """
    Use a pool manager to make safe requests.

    :return: A place to make safe requests from.
    """
    return urllib3.PoolManager(
        ca_certs=certifi.where()
    )


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
                response = safe_request().request("POST", url, fields=json)
            else:
                response = safe_request().request("GET", url)
            return json.loads(response.data)
        except Exception as error:
            time.sleep(time_between)
            count += 1
            if count >= max_retry:
                raise error
    raise ConnectionError(f'Unable to connect to {url}')
