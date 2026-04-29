import time
from dataclasses import dataclass
from random import randint
from typing import Iterable, Optional, List

from facebook_simple_scraper.details.repository import PostDetailRepository, PostDetails
from facebook_simple_scraper.entities import StopCondition, Post, PostList
from facebook_simple_scraper.posts.summary_extractor import PostSummaryHTMLParser
from facebook_simple_scraper.requester import requester


@dataclass
class GetPostOptions:
    requester: requester.Requester
    parser: PostSummaryHTMLParser
    sleep_time_min: int = 5
    sleep_time_max: int = 10
    max_comments: int = 10
    comments_repository: Optional[PostDetailRepository] = None
    stop_conditions: Optional[List[StopCondition]] = None


class PostSummaryListRepository:
    _profile_id: Optional[str]
    _cursor: Optional[str]
    _requester: requester.Requester
    _sleep_time_min: int
    _sleep_time_max: int

    def __init__(self, opts: GetPostOptions):
        self._requester = opts.requester
        self._cursor = None
        self._profile_id = None
        self._parser = opts.parser
        self._sleep_time_min = opts.sleep_time_min
        self._sleep_time_max = opts.sleep_time_max
        self._max_comments = opts.max_comments
        self._comments_repository = opts.comments_repository

    def get_posts(self, account_name: str, stop_conditions: List[StopCondition]) -> Iterable[Post]:
        post_list: List[Post] = []
        while True:
            if self._cursor is None:
                page_html = self._get_posts_first_page_html(account_name)
            else:
                page_html = self._get_posts_next_page_html(self._cursor, self._profile_id)
            r = self._parser.extract_posts(page_html)
            self._profile_id = r.profile_id
            self._cursor = r.cursor
            for post in r.posts:
                if self._max_comments > 0 and self._comments_repository is not None:
                    details = self.get_post_details(post.id)
                    if details.reactions not in [None, []]:
                        post.reactions = details.reactions
                    post.comments = details.comments
                    post.share_count = details.share_count
                    post.view_count = details.view_count

                post_list.append(post)
                yield post
            if not self._cursor:
                break
            for cond in stop_conditions:
                if cond.should_stop(post_list):
                    return
            self._sleep()

    def get_post_details(self, post_id: str) -> Optional[PostDetails]:
        return self._comments_repository.get_details(post_id, self._max_comments)

    def get_cursor(self) -> Optional[str]:
        return self._cursor

    def _sleep(self):
        time.sleep(randint(self._sleep_time_min, self._sleep_time_max))

    def _get_posts_first_page_html(self, account_name: str) -> str:
        url = f"https://mbasic.facebook.com/{account_name}?v=timeline"
        response = self._requester.request("GET", url)
        return response.text

    def _get_posts_next_page_html(self, cursor: str, profile_id: str) -> str:
        url = f"https://mbasic.facebook.com/profile/timeline/stream/"
        params = {
            "cursor": cursor,
            "profile_id": profile_id,
        }
        qp = "&".join([f"{k}={v}" for k, v in params.items()])
        url = f"{url}?{qp}"
        response = self._requester.request("GET", url)
        return response.text

    def _parse_posts_html_first_page(self, page_html: str) -> PostList:
        return self._parser.extract_posts(page_html)

    def _parse_posts_html_next_page(self, page_html: str) -> PostList:
        return self._parser.extract_posts(page_html)
