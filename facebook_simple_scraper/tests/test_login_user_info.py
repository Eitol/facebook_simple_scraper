import unittest

from facebook_simple_scraper.login.user_info import UserInfoExtractor
from facebook_simple_scraper.tests.utils import read_test_file

LOGIN_SUCCESS_COMPLETE = "../tests/files/login_success_complete.html"
LOGIN_SUCCESS_COMPLETE_2 = "../tests/files/login_success_complete_2.html"


class TestUserInfoExtractor(unittest.TestCase):
    def setUp(self):
        self.extractor = UserInfoExtractor()
        self.expected_username = 'suprapapo2222'
        self.expected_profile_name = 'Luis Zarate'
        self.expected_target = '100054215241418'
        self.expected_fb_dtsg = 'NAcMUEjl5DFOE99w2q6jpBuFciynbgnPaBeqaBsGCYf6vTB1H25vGnA:34:1716149472'

    def test_extract_user_info_valid_html(self):
        html = read_test_file(LOGIN_SUCCESS_COMPLETE)
        result = self.extractor.extract_user_info(html)
        self.assertEqual(result.username, self.expected_username)
        self.assertEqual(result.profile_name, self.expected_profile_name)
        self.assertEqual(result.target, self.expected_target)
        self.assertEqual(result.fb_dtsg, self.expected_fb_dtsg)

    def test_extract_user_info_valid_2_html(self):
        html = read_test_file(LOGIN_SUCCESS_COMPLETE_2)
        result = self.extractor.extract_user_info(html)
        self.assertEqual(result.username, self.expected_username)
        self.assertEqual(result.profile_name, self.expected_profile_name)


if __name__ == '__main__':
    unittest.main()
