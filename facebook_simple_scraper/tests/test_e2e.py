import unittest

from facebook_simple_scraper.details.repository import GraphqlCommentsRepository
from facebook_simple_scraper.posts.summary_extractor import PostSummaryListExtractor
from facebook_simple_scraper.posts.summary_repository import GetPostOptions, PostSummaryListRepository
from facebook_simple_scraper.stop_conditions import StopAfterNPosts
from facebook_simple_scraper.tests.test_login import exec_real_login_test


class TestE2E(unittest.TestCase):

    def test_e2e(self):
        req = exec_real_login_test(self)
        repo = PostSummaryListRepository(GetPostOptions(
            requester=req,
            parser=PostSummaryListExtractor(),
            sleep_time_min=1,
            sleep_time_max=2,
            comments_repository=GraphqlCommentsRepository(req),
            max_comments=10
        ))
        gen = repo.get_posts('NintendoLatAm', [StopAfterNPosts(2)])
        posts = list(gen)
        for post in posts:
            self.assertGreater(len(posts), 0)
            self.assertIsNotNone(post.id)
            self.assertIsNotNone(post.text)
            self.assertIsNotNone(post.date)
