import unittest

from facebook_simple_scraper.entities import ScraperOptions, LoginCredentials
from facebook_simple_scraper.scraper import Scraper
from facebook_simple_scraper.stop_conditions import StopAfterNPosts
from facebook_simple_scraper.tests.utils import get_real_test_credentials


class TestPostExtractor(unittest.TestCase):
    def test_scraper(self):
        user, password = get_real_test_credentials()
        opts = ScraperOptions(
            credentials=[LoginCredentials(
                username=user,
                password=password
            )],
            max_comments_per_post=10,
            sleep_time_min=2,
            sleep_time_max=5,
            stop_conditions=[StopAfterNPosts(5)],
        )
        scraper = Scraper(opts)
        post = scraper.get_posts("NintendoLatAm")
        print(list(post))

