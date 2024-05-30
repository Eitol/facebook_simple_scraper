import unittest
from typing import List

from facebook_simple_scraper.posts.summary_extractor import PostSummaryListExtractor
from facebook_simple_scraper.posts.summary_repository import PostSummaryListRepository, GetPostOptions
from facebook_simple_scraper.stop_conditions import StopAfterNPosts
from facebook_simple_scraper.tests.test_post import POST_TEST_FIRST_FILE_HTML, POST_TEST_SECOND_FILE_HTML, \
    POST_TEST_LAST_FILE_HTML
from facebook_simple_scraper.tests.utils import MockRequester, read_test_file


class TestPostSummaryListRepository(unittest.TestCase):

    def test_get_posts_first_page(self):
        self.get_posts(pages=[1])
        self.get_posts(pages=[1, 3])
        self.get_posts(pages=[1, 2, 3])

    def get_posts(self, pages: List[int]):
        req = MockRequester()
        if 1 in pages:
            req.add_expected_response(
                r_text=read_test_file(POST_TEST_FIRST_FILE_HTML)
            )
        if 2 in pages:
            req.add_expected_response(
                r_text=read_test_file(POST_TEST_SECOND_FILE_HTML)
            )
        if 3 in pages:
            req.add_expected_response(
                r_text=read_test_file(POST_TEST_LAST_FILE_HTML)
            )
        opts = GetPostOptions(
            requester=req,
            parser=PostSummaryListExtractor(),
            sleep_time_max=0,
            sleep_time_min=0
        )
        repo = PostSummaryListRepository(opts=opts)
        posts = list(repo.get_posts('username', [StopAfterNPosts(10)]))
        self.assertIsInstance(posts, list)


if __name__ == '__main__':
    unittest.main()
