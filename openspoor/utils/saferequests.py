import time
import json
import certifi
import urllib3
from typing import Optional

from openspoor.utils.singleton import Singleton


class SafeRequest(Singleton):

    last_request = 0  # Use a class attribute, as we use the Singleton pattern

    def __init__(self, max_retry: int = 5, time_between: float = 1.0):
        """
        Create a package from where we can make requests. The requests are done using certificates and a sleep is
        built in to guarantee that there is some time between every API call.

        :param max_retry: The maximum amount of times a request is attempted
        :param time_between: The minimum time between two consecutive queries
        """
        self.pool = urllib3.PoolManager(ca_certs=certifi.where())
        self.max_retry = max_retry
        self.time_between = time_between

    def force_time_between_and_retry(func):
        def retryer(self, request_type: str, url: str, body: Optional[dict] = None, *args, **kwargs):
            count = 0
            while count <= self.max_retry:
                try:
                    time_since_last = time.time() - SafeRequest.last_request
                    if time_since_last < self.time_between:
                        time.sleep(self.time_between - time_since_last)
                    SafeRequest.last_request = time.time()  # Do this before the query to update even if unsuccessful
                    return func(self, request_type, url, body)
                except Exception as error:
                    print(error)
                    count += 1
                    if count >= self.max_retry:
                        raise error
            raise ConnectionError(f'Unable to connect to {url}')

        return retryer

    @force_time_between_and_retry
    def _request(self, request_type: str, url: str, body: Optional[dict] = None) -> urllib3.response.HTTPResponse:
        """
        Make an API call using a certificate

        :param request_type: The request type to use
        :param url: The URL to query
        :param body: A dictionary to be passed as a body
        :return: An http response
        """
        if isinstance(body, dict):
            body = json.dumps(body)
        return self.pool.request(request_type, url, body=body)

    def get_string(self, request_type: str, url: str, body: Optional[dict] = None):
        """
        Return a request as a string.

        :param request_type: The request type to use
        :param url: The URL to query
        :param body: A dictionary to be passed as a body
        :return: The output of the request as a string
        """

        return self._request(request_type, url, body)._body.decode('UTF-8')

    def get_json(self, request_type: str, url: str, body: Optional[dict] = None) -> dict:
        """
        Return a request as a dictionary.

        :param request_type: The request type to use
        :param url: The URL to query
        :param body: A dictionary to be passed as a body
        :return: The output body of the request as a dictionary
        """
        return json.loads(self.get_string(request_type, url, body))

    def get_data(self, request_type: str, url: str, body: Optional[dict] = None) -> dict:
        """
        Return the request data as a dictionary.

        :param request_type: The request type to use
        :param url: The URL to query
        :param body: A dictionary to be passed as a body
        :return: The output data of the request as a dictionary
        """
        return json.loads(self._request(request_type, url, body).data)
