import time
from typing import Tuple
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from facebook_simple_scraper.entities import SessionStorage, UserInfo
from facebook_simple_scraper.error_dict import SessionNotFoundError, SessionExpiredError, LoginFailedException, \
    ApiError
from facebook_simple_scraper.login.domain import LoginRepository, LoginResponse
from facebook_simple_scraper.login.params import LoginParamsRepository
from facebook_simple_scraper.login.urls import FB_MBASIC_LOGIN_PAGE_URL, FB_MBASIC_PAGE_URL
from facebook_simple_scraper.login.user_info import UserInfoExtractor
from facebook_simple_scraper.requester.requester import Requester


class MobileBasicLoginRepository(LoginRepository):
    def __init__(self, params_repo: LoginParamsRepository, session_storage: SessionStorage, requester: Requester):
        self._params_repo = params_repo
        self._session_storage = session_storage
        self._requester = requester
        self._user_info_extractor = UserInfoExtractor()

    def login(self, username: str, password: str) -> LoginResponse:
        try:
            current_session = self._session_storage.get_requester(username)
        except SessionNotFoundError:
            # TODO: Add logging and callbacks
            current_session = None
        except SessionExpiredError:
            # TODO: Add logging and callbacks
            current_session = None
        except Exception:
            current_session = None
            pass  # TODO: Add logging and callbacks
        if current_session is not None:
            self._requester = current_session
            return LoginResponse(False, False, requester=current_session)

        return self._do_server_auth(username, password)

    def _do_server_auth(self, username: str, password: str) -> LoginResponse:
        params = self._params_repo.get_login_params()
        url = f"{FB_MBASIC_LOGIN_PAGE_URL}/device-based/regular/login/?refsrc=deprecated&lwv=100"
        payload = {
            'lsd': params.lsd,
            'jazoest': params.jazoest,
            'm_ts': int(time.time()),
            'li': params.li,
            'try_number': 0,
            'unrecognized_tries': 0,
            'email': username,
            'pass': password,
            'bi_xrwh': 0,
            'login': 'Iniciar sesión',
        }
        headers = {
            'referer': f'{FB_MBASIC_LOGIN_PAGE_URL}/?refsrc=deprecated&_rdr'
        }
        response = self._requester.request("POST", url, data=payload, headers=headers)
        if 'password_failure' in response.text:
            raise LoginFailedException(username)
        if "<head><title>Error</title></head>" in response.text:
            raise ApiError(response.text)
        was_checkpoint, cp_req = self._check_challenge(BeautifulSoup(response.text, 'html.parser'), False, response)
        params_1: dict = {}
        params_3: dict = {}
        params_4: dict = {}
        if was_checkpoint:
            try:
                params_3 = self._params_repo.extract_params_from_html(response.text).__dict__
            except Exception:
                pass
            response = cp_req

        if '/login/device-based/update-nonce/?paipv' in response.text:
            params_4 = self._params_repo.extract_params_from_html(response.text).__dict__
            text = self._send_save_device_request(response.text)
            save_device = True
            params_2 = self._params_repo.extract_params_from_html(text).__dict__
        else:
            save_device = False
            text = response.text
            params_2 = self._params_repo.extract_params_from_html(text).__dict__

        try:
            user_info = self._extract_user_info(text)
        except LoginFailedException:
            raise LoginFailedException(f"user: '{username}' password: '{password}'")
        except Exception:
            raise LoginFailedException("Error while extracting user info")

        session_vars = user_info.__dict__
        self._merge_dicts(params_1, session_vars)
        self._merge_dicts(params_2, session_vars)
        self._merge_dicts(params_3, session_vars)
        self._merge_dicts(params_4, session_vars)
        self._requester.save_session_variables(session_vars)
        try:
            self._session_storage.save_requester(username, self._requester)
        except Exception:
            # TODO: Add logging and callbacks
            pass
        return LoginResponse(
            was_logged=True,
            save_device=save_device,
            user_info=user_info,
            requester=self._requester,
        )

    @staticmethod
    def _merge_dicts(params_1: dict, session_vars: dict) -> dict:
        for key, value in params_1.items():
            if value is not None and value != '':
                session_vars[key] = value
        return session_vars

    def _send_save_device_request(self, html_resp: str) -> str:
        soup = BeautifulSoup(html_resp, 'html.parser')
        form = soup.find('form')

        # Extraer la URL de acción del formulario
        action_url = form['action']
        # Extraer los datos del formulario
        form_data = {}
        for input_tag in form.find_all('input'):
            name = input_tag.get('name')
            value = input_tag.get('value')
            if name and value is not None:
                form_data[name] = value

        url = f"{FB_MBASIC_PAGE_URL}{action_url}"
        # Enviar la solicitud POST con los datos del formulario
        response = self._requester.request("POST", url, data=form_data)
        return response.text

    def _extract_user_info(self, html_resp: str) -> UserInfo:
        return self._user_info_extractor.extract_user_info(html_resp)

    def _check_challenge(self, soup: BeautifulSoup, was_challenge: bool,
                         latest_resp: requests.Response) -> Tuple[bool, requests.Response]:
        checkpoint_form = soup.find('form', action='/login/checkpoint/')
        if not checkpoint_form:
            return was_challenge, latest_resp

        inputs = checkpoint_form.find_all('input')
        valid_inputs = []
        for i in inputs:
            if i.get('value') is not None and i.get('type') != 'submit':
                valid_inputs.append(i)
        submit = soup.find('input', id="checkpointSubmitButton-actual-button")
        if not submit:
            raise LoginFailedException("Login failed: checkpoint form without submit button")
        values = {i.get('name'): i.get('value') for i in valid_inputs}
        values[submit.get("name")] = submit.get('value')
        lr = self._requester.get_latest_request()
        if lr is None:
            raise LoginFailedException("No latest request found")
        parsed_url = urlparse(lr.url)
        url = f"{parsed_url.scheme}://{parsed_url.netloc}{checkpoint_form['action']}"
        print("\n\n-------------------\n\n")
        print("Challenge required!")
        print()
        print("Sleep for 20 seconds and retrying.")
        print("\n\n-------------------\n\n")
        time.sleep(20)
        resp = self._requester.request('POST', url, data=values)
        soup = BeautifulSoup(resp.text, 'html.parser')
        checkpoint_form = soup.find('form', action='/login/checkpoint/')
        if checkpoint_form:
            return self._check_challenge(soup, True, resp)

        print("\n\n-------------------\n\n")
        print("INFO: Challenge passed.")
        print("\n\n-------------------\n\n")
        return True, resp
