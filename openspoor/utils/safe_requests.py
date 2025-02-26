import json
import logging
import ssl
import time
from typing import Optional

import certifi
import urllib3
from requests.exceptions import SSLError

from openspoor.utils.singleton import Singleton


class SafeRequest(Singleton):
    """
    A class for making requests with a delay between them.
    """

    last_request = (
        0.0  # Use a class attribute, as we use the Singleton pattern
    )

    def __init__(self, max_retry: int = 5, time_between: float = 0.3):
        """
        Requests are performed using certificates, and a delay is built in to
        ensure a minimum time between consecutive API calls.

        Parameters
        ----------
        max_retry : int
            The maximum number of times a request is attempted.
        time_between : float
            The minimum time (in seconds) between two consecutive queries.
        """

        # Hotfix: Updates to SSL certificates were required.
        # See https://stackoverflow.com/questions/71603314/ssl-error-unsafe-legacy-renegotiation-disabled  # noqa
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ctx.options |= 0x4
        self.pool = urllib3.PoolManager(
            ca_certs=certifi.where(), ssl_context=ctx
        )
        self.max_retry = max_retry
        self.time_between = time_between

    def _request_with_retry(
        self, request_type: str, url: str, body: Optional[dict] = None
    ) -> urllib3.response.BaseHTTPResponse:
        """
        Make an API call using a certificate.

        Ensures the time between consecutive calls is
        at least `self.time_between`
        seconds and retries for the required number of times.

        Parameters
        ----------
        request_type : str
            The request type to use (e.g., "GET", "POST").
        url : str
            The URL to query.
        body : dict, optional
            A dictionary to be passed as the request body.

        Returns
        -------
        http.Response
            The HTTP response object.
        """
        body_str: Optional[str] = None
        if isinstance(body, dict):
            body_str = json.dumps(body)

        count = 0
        while count <= self.max_retry:
            try:
                time_since_last = time.time() - SafeRequest.last_request
                time.sleep(max(0.0, self.time_between - time_since_last))
                SafeRequest.last_request = (
                    time.time()
                )  # Do this before the query to update even if unsuccessful
                request = self.pool.request_encode_body(
                    request_type, url, body=body_str  # type: ignore
                )
                if request.status == 200:
                    return request
                else:
                    raise ConnectionError(
                        f"Status {request.status} received at"
                        f"{url} instead of 200"
                    )

            except SSLError:
                logging.warning(
                    "Removing certificates. "
                    "Please be aware of the security risks."
                )
                self.pool = urllib3.PoolManager()
            except Exception as error:
                count += 1
                logging.warning(
                    "Error encountered performing attempt %d out of %d",
                    count,
                    self.max_retry,
                )
                logging.warning(error)
                if count >= self.max_retry:
                    raise error
        raise ConnectionError(
            f"Could not connect to {url} after {self.max_retry} attempts"
        )

    def get_string(
        self, request_type: str, url: str, body: Optional[dict] = None
    ):
        """
        Return a request as a string.

        Parameters
        ----------
        request_type : str
            The request type to use (e.g., "GET", "POST").
        url : str
            The URL to query.
        body : dict, optional
            A dictionary to be passed as the request body.

        Returns
        -------
        str
            The output of the request as a string.
        """

        return self._request_with_retry(request_type, url, body).data.decode(
            "UTF-8"
        )

    def get_json(
        self, request_type: str, url: str, body: Optional[dict] = None
    ) -> dict:
        """
        Return the request data as a dictionary.

        Parameters
        ----------
        request_type : str
            The request type to use (e.g., "GET", "POST").
        url : str
            The URL to query.
        body : dict, optional
            A dictionary to be passed as the request body.

        Returns
        -------
        dict
            The output data of the request as a dictionary.
        """
        return json.loads(self.get_string(request_type, url, body))
