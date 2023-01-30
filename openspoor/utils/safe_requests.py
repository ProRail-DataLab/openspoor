import time
import json
import certifi
import urllib3
from typing import Optional
import logging
import ssl
from requests.exceptions import SSLError

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

        # Hotfix: Updates to SSL certificates were required.
        # See https://stackoverflow.com/questions/71603314/ssl-error-unsafe-legacy-renegotiation-disabled
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ctx.options |= 0x4
        self.pool = urllib3.PoolManager(ca_certs=certifi.where(), ssl_context=ctx)
        self.max_retry = max_retry
        self.time_between = time_between


    def _request_with_retry(self, request_type: str, url: str, body: Optional[dict] = None)\
            -> urllib3.response.HTTPResponse:
        """
        Make an API call using a certificate. Ensure the time between consecutive calls is at least self.time_between
        seconds and retry for the required amount of times.

        :param request_type: The request type to use
        :param url: The URL to query
        :param body: A dictionary to be passed as a body
        :return: An http response
        """
        if isinstance(body, dict):
            body = json.dumps(body)

        count = 0
        while count <= self.max_retry:
            try:
                time_since_last = time.time() - SafeRequest.last_request
                time.sleep(max(0.0, self.time_between - time_since_last))
                SafeRequest.last_request = time.time()  # Do this before the query to update even if unsuccessful
                request = self.pool.request(request_type, url, body=body)
                if request.status == 200:
                    return request
                else:
                    raise ConnectionError(f'Status {request.status} received at {url} instead of 200')

            except SSLError:
                logging.warning("Removing certificates. Please be aware of the security risks.")
                self.pool = urllib3.PoolManager()
            except Exception as error:
                count += 1
                logging.warning(f'Error encountered performing attempt {count} out of {self.max_retry}')
                logging.warning(error)
                if count >= self.max_retry:
                    raise error

    def get_string(self, request_type: str, url: str, body: Optional[dict] = None):
        """
        Return a request as a string.

        :param request_type: The request type to use
        :param url: The URL to query
        :param body: A dictionary to be passed as a body
        :return: The output of the request as a string
        """

        return self._request_with_retry(request_type, url, body).data.decode('UTF-8')

    def get_json(self, request_type: str, url: str, body: Optional[dict] = None) -> dict:
        """
        Return the request data as a dictionary.

        :param request_type: The request type to use
        :param url: The URL to query
        :param body: A dictionary to be passed as a body
        :return: The output data of the request as a dictionary
        """
        return json.loads(self.get_string(request_type, url, body))
