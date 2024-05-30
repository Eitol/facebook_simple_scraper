import re
import unittest

from facebook_simple_scraper.login.params import LoginParams, MbasicLoginParamsRepository
from facebook_simple_scraper.tests.utils import MockRequester, read_test_file

LOGIN_PARAM_TEST_FILE = '../tests/files/login_param_page_example.html'

TEST_JAZOEST_REGEX = re.compile(r'2(\d+)')
TEST_LSD_REGEX = re.compile(r'([A-Za-z0-9]+)')
TEST_LI_REGEX = re.compile(r'([A-Za-z0-9_]+)')


class TestPageLoginParamsRepository(unittest.TestCase):

    def test_get_login_params(self):
        req = MockRequester()
        req.add_expected_response(
            r_text=read_test_file(LOGIN_PARAM_TEST_FILE)
        )
        repository = MbasicLoginParamsRepository(req)
        result = repository.get_login_params()
        self.assertIsInstance(result, LoginParams)
        self.assertRegex(result.jazoest, TEST_JAZOEST_REGEX)
        self.assertRegex(result.lsd, TEST_LSD_REGEX)
        self.assertRegex(result.li, TEST_LI_REGEX)


if __name__ == "__main__":
    unittest.main()
