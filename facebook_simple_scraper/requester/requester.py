import abc
import datetime
from dataclasses import dataclass
from typing import Optional

import requests

from facebook_simple_scraper.error_dict import SessionExpiredError
from facebook_simple_scraper.requester.headers import DEFAULT_HEADER


@dataclass
class HttpResponse:
    status_code: int
    body: str
    headers: dict


class Requester(abc.ABC):
    @abc.abstractmethod
    def request(self, method: str, url: str, data: Optional[dict] = None, headers: Optional[dict] = None) -> requests.Response:
        raise NotImplementedError()

    @abc.abstractmethod
    def validate(self) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def save_session_variables(self, session_variables: dict) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def load_session_variables(self) -> dict:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_latest_request(self) -> Optional[requests.Request]:
        raise NotImplementedError()


class FacebookSessionBasedRequester(Requester):

    def __init__(self, session: Optional[requests.Session] = None, base_headers: Optional[dict] = None):
        if session is None:
            self.session = requests.Session()
        else:
            self.session = session
        if base_headers is not None:
            self.headers = base_headers
        else:
            self.headers = DEFAULT_HEADER
        self.session_variables: dict = {}
        self.latest_request: Optional[requests.Request] = None

    def load_session_variables(self) -> dict:
        return self.session_variables

    def save_session_variables(self, session_variables: dict) -> None:
        self.session_variables = session_variables

    def validate(self) -> None:
        self._check_cookie_expiry(self.session)

    @staticmethod
    def _check_cookie_expiry(session: requests.Session) -> None:
        for cookie in session.cookies:
            if cookie.name == 'datr':
                expiry = cookie.expires
                if expiry and datetime.datetime.fromtimestamp(expiry) < datetime.datetime.now():
                    raise SessionExpiredError(datetime.datetime.fromtimestamp(expiry))
                else:
                    return
        raise ValueError("Session has no 'datr' cookie")

    def request(self, method: str, url: str, data: Optional[dict] = None,
                headers: Optional[dict] = None) -> requests.Response:
        if headers is not None:
            for k, v in self.headers.items():
                if k not in headers:
                    headers[k] = v
        else:
            headers = self.headers
        self.latest_request = requests.Request(method, url, headers=headers, data=data)
        return self.session.request(method, url, data=data, headers=headers)

    def get_session(self) -> requests.Session:
        return self.session

    def get_latest_request(self) -> Optional[requests.Request]:
        return self.latest_request
