import datetime
import pickle
import shutil
import tempfile
import unittest
from http.cookiejar import Cookie
from typing import Optional

import requests

from facebook_simple_scraper.error_dict import SessionNotFoundError, SessionExpiredError
from facebook_simple_scraper.login.session_storage import LocalFileSessionStorage
from facebook_simple_scraper.requester import requester


class TestLocalFileSessionStorage(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.storage = LocalFileSessionStorage(self.test_dir)
        self.username = "testuser"

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @staticmethod
    def create_test_requester(expires: Optional[datetime.datetime] = None) -> requester.Requester:
        session = requests.Session()
        cookie = Cookie(
            version=0, name='datr', value='B9YvZsAqz0xI6TKUYlYrtRJK',
            port=None, port_specified=False, domain='facebook.com', domain_specified=True, domain_initial_dot=False,
            path='/', path_specified=True, secure=True, expires=int(expires.timestamp()) if expires else None,
            discard=False, comment=None, comment_url=None, rest={'HttpOnly': 'null'}, rfc2109=False
        )
        session.cookies.set_cookie(cookie)
        return requester.FacebookSessionBasedRequester(session)

    def test_save_and_get_session(self):
        r = self.create_test_requester(expires=datetime.datetime.now() + datetime.timedelta(days=1))
        self.storage.save_requester(self.username, r)

        loaded_requester = self.storage.get_requester(self.username)
        loaded_requester.validate()

    def test_expired_cookie_raises_exception(self):
        expired_date = datetime.datetime.now() - datetime.timedelta(days=1)
        r = self.create_test_requester(expires=expired_date)
        session_filepath = self.storage._get_session_filepath(self.username)

        with open(session_filepath, 'wb') as f:
            pickle.dump(r, f)

        with self.assertRaises(SessionExpiredError):
            self.storage.get_requester(self.username)

    def test_no_session_file_raises_exception(self):
        with self.assertRaises(SessionNotFoundError):
            self.storage.get_requester(self.username)


if __name__ == '__main__':
    unittest.main()
