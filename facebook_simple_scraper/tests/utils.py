import json
import os
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple, List

import requests

from facebook_simple_scraper.entities import Post
from facebook_simple_scraper.requester.requester import Requester


def read_test_file(file_path) -> str:
    with open(file_path, 'r') as file:
        return file.read()


def get_real_test_credentials() -> Tuple[str, str]:
    if 'FACEBOOK_USER' not in os.environ:
        return "", ""
    if 'FACEBOOK_PASSWORD' not in os.environ:
        return "", ""
    user = os.environ['FACEBOOK_USER']
    password = os.environ['FACEBOOK_PASSWORD']
    return user, password


def _load_expected_posts(file_path: Path) -> List[Post]:
    expected_result_json = json.loads(read_test_file(file_path))
    expected: List[Post] = []
    for expected_post_dict in expected_result_json:
        expected.append(Post(**expected_post_dict))
    return expected


class MockRequester(Requester):
    session_variables: dict = {}
    responses: List[requests.Response] = []
    last_request_history: List[requests.Request] = []

    def save_session_variables(self, session_variables: dict) -> None:
        self.session_variables = session_variables

    def load_session_variables(self) -> dict:
        return self.session_variables

    def clear(self):
        self.responses = []
        self.last_request_history = []

    def add_expected_response(self, resp_text: Optional[str] = None, status_code: int = 200, resp_headers: Optional[dict] = None):
        if resp_text is None:
            resp_text = ""
        response = requests.Response()
        response.headers = resp_headers if resp_headers is not None else {}
        response.raw = BytesIO(resp_text.encode())
        response.status_code = status_code
        self.responses.append(response)

    def request(self, method: str, url: str, data: Optional[dict] = None, headers: Optional[dict] = None) -> requests.Response:
        self.last_request_history.append(requests.Request(method, url, headers, data))
        resp = self.responses[0]
        self.responses = self.responses[1:]
        return resp

    def validate(self) -> None:
        pass

    def get_latest_request(self) -> Optional[requests.Request]:
        return self.last_request_history[-1]
