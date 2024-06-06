import abc
import base64
import json
import time
from typing import Optional

import requests

from facebook_simple_scraper.details.extractor import GQLPostDetailExtractor, PostDetails
from facebook_simple_scraper.requester.requester import Requester


class PostDetailRepository(abc.ABC):
    @abc.abstractmethod
    def get_details(self, post_id: str, max_comments: int) -> Optional[PostDetails]:
        raise NotImplementedError()


class GraphqlCommentsRepository(PostDetailRepository):

    def __init__(self, requester: Requester, await_time: int = 1):
        self.requester = requester
        self._cursor = None
        self._extractor = GQLPostDetailExtractor()
        self._await_time = await_time
        self._no_auth_session = requests.Session()

    def get_details(self, post_id: str, max_comments: int) -> Optional[PostDetails]:
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
            response = self._no_auth_session.request("POST", url, headers=headers, data=payload_dict)
            detail = self._extractor.extract(response.text)
            all_comments.extend(detail.comments)
            if detail.next_cursor is None or len(all_comments) >= max_comments:
                break
            self._cursor = detail.next_cursor
            if self._cursor is None or self._cursor == "":
                break
            time.sleep(self._await_time)
        self._cursor = None
        return detail

    def _build_payload(self, post_id, vars_dict: dict):
        target = vars_dict['target']
        # variables = {
        #     "commentsAfterCount": -1,
        #     "commentsIntentToken": "RANKED_UNFILTERED_CHRONOLOGICAL_REPLIES_INTENT_V1",
        #     "feedLocation": "DEDICATED_COMMENTING_SURFACE",
        #     "scale": 2,
        #     "useDefaultActor": False,
        #     "feedbackID": base64.b64encode(bytes(f"feedback:{post_id}", 'utf-8')).decode('utf-8'),
        # }
        variables = {
            "feedbackID": base64.b64encode(bytes(f"feedback:{post_id}", 'utf-8')).decode('utf-8'),
            "feedbackSource": 110,
            "feedLocation": "DEDICATED_COMMENTING_SURFACE",
            "scale": 2,
            "storyID": base64.b64encode(bytes(f"S:_I{post_id}:{target}:{target}", 'utf-8')).decode('utf-8'),
            "__relay_internal__pv__CometIsAdaptiveUFIEnabledrelayprovider": False,
            "__relay_internal__pv__CometUFIShareActionMigrationrelayprovider": True,
            "__relay_internal__pv__CometUFIReactionsEnableShortNamerelayprovider": True
        }
        if self._cursor is not None:
            variables["commentsAfterCursor"] = self._cursor

        payload_dict = {
            # "fb_api_req_friendly_name": "CometFocusedStoryViewUFIQuery",
            # "fb_dtsg": vars_dict['fb_dtsg'],
            "variables": json.dumps(variables),
            "doc_id": 7918407668226884
        }
        return payload_dict

    @staticmethod
    def _build_headers():
        headers = {
            # 'accept': '*/*',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://web.facebook.com',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            # "accept-language": "es,en-US;q=0.9,en;q=0.8,pt;q=0.7",
            # "priority": "u=1, i",
            # "sec-ch-prefers-color-scheme": "dark",
            # "sec-ch-ua": "\"Chromium\"\";v=\"124\", \"Google Chrome\";v=\"124\", \"Not-A.Brand\";v=\"99\"\"",
            # "sec-ch-ua-full-version-list": "\"Chromium\";v=\"124.0.6367.93\",
            # \"Google Chrome\";v=\"124.0.6367.93\", \"Not-A.Brand\";v=\"99.0.0.0\"",
            # "sec-ch-ua-mobile": "?0",
            # "sec-ch-ua-model": "\"\"",
            # "sec-ch-ua-platform": "\"macOS\"",
            # "sec-ch-ua-platform-version": "\"14.4.1\"",
            # "sec-fetch-dest": "empty",
            # "sec-fetch-mode": "cors",
            # "x-asbd-id": "129477",
            # "x-fb-friendly-name": "CometFocusedStoryViewUFIQuery",
            # "x-fb-lsd": "fm9k1VDD3N5sTCvIO9jiuc"
        }
        return headers
