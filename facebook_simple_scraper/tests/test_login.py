import os
import tempfile
import unittest

from facebook_simple_scraper.error_dict import LoginFailedException
from facebook_simple_scraper.login.domain import LoginResponse
from facebook_simple_scraper.login.login import MobileBasicLoginRepository
from facebook_simple_scraper.login.params import MbasicLoginParamsRepository
from facebook_simple_scraper.login.session_storage import LocalFileSessionStorage
from facebook_simple_scraper.requester import requester
from facebook_simple_scraper.tests.test_login_params import LOGIN_PARAM_TEST_FILE
from facebook_simple_scraper.tests.test_login_user_info import LOGIN_SUCCESS_COMPLETE
from facebook_simple_scraper.tests.utils import read_test_file, MockRequester

SUCCESS_LOGIN_PAGE_TEST_FILE = '../tests/files/login_success.html'
FAILED_LOGIN_PAGE_TEST_FILE = '../tests/files/login_failure.html'


class TestLogin(unittest.TestCase):
    def setUp(self):
        self.requester = MockRequester()
        self.params_repo = MbasicLoginParamsRepository(self.requester)
        self.temp_dir = tempfile.TemporaryDirectory()
        self.session_storage = LocalFileSessionStorage(self.temp_dir.name)
        self.login_repo = MobileBasicLoginRepository(
            self.params_repo,
            session_storage=self.session_storage,
            requester=self.requester,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_login_success(self):
        self.requester.clear()
        self.requester.add_expected_response(
            r_text=read_test_file(LOGIN_PARAM_TEST_FILE)
        )
        self.requester.add_expected_response(
            r_text=read_test_file(SUCCESS_LOGIN_PAGE_TEST_FILE)
        )
        self.requester.add_expected_response(
            r_text=read_test_file(LOGIN_SUCCESS_COMPLETE)
        )
        res = self.login_repo.login('username', 'password')
        self.assertIsInstance(res, LoginResponse)

    def test_login_failed(self):
        self.requester.clear()
        self.requester.add_expected_response(
            r_text=read_test_file(LOGIN_PARAM_TEST_FILE)
        )
        self.requester.add_expected_response(
            r_text=read_test_file(FAILED_LOGIN_PAGE_TEST_FILE)
        )
        with self.assertRaises(LoginFailedException):
            self.login_repo.login('username', 'password')

    def test_login_real_success(self):
        exec_real_login_test(self)


def exec_real_login_test(t: unittest.TestCase) -> requester.Requester:
    if 'FACEBOOK_USER' not in os.environ:
        t.skipTest('No test user configured')
    if 'FACEBOOK_PASSWORD' not in os.environ:
        t.skipTest('No test password configured')
    user = os.environ['FACEBOOK_USER']
    password = os.environ['FACEBOOK_PASSWORD']
    req = requester.FacebookSessionBasedRequester()
    params_repo = MbasicLoginParamsRepository(req)
    repo = MobileBasicLoginRepository(
        params_repo,
        session_storage=LocalFileSessionStorage('real'),
        requester=req
    )
    res = repo.login(user, password)
    if res.was_logged:
        t.assertIsInstance(res, LoginResponse)
    if res.requester is None:
        t.fail('Requester not set')
    return res.requester


if __name__ == '__main__':
    unittest.main()
