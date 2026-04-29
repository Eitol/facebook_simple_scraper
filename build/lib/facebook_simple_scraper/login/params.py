from typing import Optional, Dict, List

from bs4 import BeautifulSoup

from facebook_simple_scraper.login.domain import LoginParamsRepository, LoginParams
from facebook_simple_scraper.login.urls import FB_MBASIC_LOGIN_PAGE_URL
from facebook_simple_scraper.requester.requester import Requester

DEFAULT_LOGIN_PARAMS_NAMES = ['jazoest', 'lsd', 'li', 'fb_dtsg', 'target']


class MbasicLoginParamsRepository(LoginParamsRepository):
    def __init__(self, requester: Requester, params_names: Optional[List[str]] = None):
        if params_names is None:
            self._params_names = DEFAULT_LOGIN_PARAMS_NAMES
        else:
            self._params_names = params_names
        self._requester = requester

    def get_login_params(self) -> LoginParams:
        fb_html_login_page = self._fetch_fb_login_page_html()
        return self.extract_params_from_html(fb_html_login_page)

    def extract_params_from_html(self, fb_html_login_page: str) -> LoginParams:
        soup = BeautifulSoup(fb_html_login_page, 'html.parser')
        inputs = soup.find_all('input', type='hidden')
        values: Dict[str, str] = {}
        for input_item in inputs:
            attrs: Dict = input_item.attrs
            if attrs is None or 'name' not in attrs or 'value' not in attrs:
                continue
            if attrs['name'] in self._params_names:
                name = input_item.attrs['name']
                values[name] = input_item.attrs['value']
                if name in values and len(values) == values[name]:
                    break
                values[name] = input_item.attrs['value']
            if len(values) == len(self._params_names):
                break
        return LoginParams(**values)

    def _fetch_fb_login_page_html(self) -> str:
        response = self._requester.request("GET", FB_MBASIC_LOGIN_PAGE_URL)
        return response.text
