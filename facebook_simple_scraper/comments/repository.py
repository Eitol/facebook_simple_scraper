import abc
import base64
import json
import time
from typing import List

from facebook_simple_scraper.comments.extractor import GQLCommentExtractor
from facebook_simple_scraper.entities import Comment
from facebook_simple_scraper.requester.requester import Requester


class CommentsRepository(abc.ABC):
    @abc.abstractmethod
    def get_comments(self, post_id: str, max_comments: int) -> List[Comment]:
        raise NotImplementedError()


class GraphqlCommentsRepository(CommentsRepository):

    def __init__(self, requester: Requester, await_time: int = 1):
        self.requester = requester
        self._cursor = None
        self._extractor = GQLCommentExtractor()
        self._await_time = await_time

    def get_comments(self, post_id: str, max_comments: int) -> List[Comment]:
        url = "https://web.facebook.com/api/graphql/"
        variables = self.requester.load_session_variables()

        if 'fb_dtsg' not in variables:
            raise Exception('No fb_dtsg found in session variables')
        if 'target' not in variables:
            raise Exception('No target found in session variables')

        all_comments = []
        while True:
            payload_dict = self._build_payload(post_id, variables)
            headers = self._build_headers()
            response = self.requester.request("POST", url, headers=headers, data=payload_dict)
            comments, cursor = self._extractor.extract(response.text)
            all_comments.extend(comments)
            if cursor is None or len(all_comments) >= max_comments:
                break
            self._cursor = cursor
            if self._cursor is None or self._cursor == "":
                break
            time.sleep(self._await_time)
        self._cursor = None
        return all_comments

    def _build_payload(self, post_id, vars_dict: dict):
        variables = {
            "commentsAfterCount": -1,
            "commentsIntentToken": "RANKED_UNFILTERED_CHRONOLOGICAL_REPLIES_INTENT_V1",
            "feedLocation": "DEDICATED_COMMENTING_SURFACE",
            "scale": 2,
            "useDefaultActor": False,
            "id": base64.b64encode(bytes(f"feedback:{post_id}", 'utf-8')).decode('utf-8'),
        }
        if self._cursor is not None:
            variables["commentsAfterCursor"] = self._cursor

        payload_dict = {
            "__ccg": "EXCELLENT",
            "fb_dtsg": vars_dict['fb_dtsg'],
            "variables": json.dumps(variables),
            "doc_id": 6944999178935452
        }
        return payload_dict

    @staticmethod
    def _build_headers():
        headers = {
            'accept': '*/*',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://web.facebook.com',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        }
        return headers
