import os
import pickle

from facebook_simple_scraper.entities import SessionStorage
from facebook_simple_scraper.error_dict import SessionNotFoundError
from facebook_simple_scraper.requester import requester


class LocalFileSessionStorage(SessionStorage):
    def __init__(self, storage_dir: str):
        self.storage_dir = storage_dir
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)

    def get_requester(self, username: str) -> requester.Requester:
        session_filepath = self._get_session_filepath(username)

        if not os.path.exists(session_filepath):
            raise SessionNotFoundError(f"No session file found for user {username}")

        with open(session_filepath, 'rb') as f:
            r: requester.Requester = pickle.load(f)
        r.validate()
        return r

    def save_requester(self, username: str, r: requester.Requester) -> None:
        session_filepath = self._get_session_filepath(username)
        try:
            with open(session_filepath, 'wb') as f:
                pickle.dump(r, f)
        except Exception as e:
            raise ValueError(f"Error saving session file for user {username}: {e}")

    def _get_session_filepath(self, username: str) -> str:
        return os.path.join(self.storage_dir, f"{username}_session.pkl")
