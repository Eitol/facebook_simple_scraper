import unittest
from pathlib import Path
from typing import List

from facebook_simple_scraper.entities import PostList
from facebook_simple_scraper.posts.summary_extractor import PostSummaryListExtractor
from facebook_simple_scraper.posts.summary_repository import PostSummaryListRepository, GetPostOptions
from facebook_simple_scraper.stop_conditions import StopAfterNPosts
from facebook_simple_scraper.tests.utils import read_test_file, MockRequester, _load_expected_posts

POST_TEST_FIRST_FILE_HTML = 'files/post_first_page.html'
POST_TEST_FIRST_FILE_JSON = 'files/post_first_page.json'

POST_TEST_SECOND_FILE_HTML = 'files/post_second_page.html'
POST_TEST_SECOND_FILE_JSON = 'files/post_second_page.json'

POST_TEST_LAST_FILE_HTML = 'files/post_last_page.html'
POST_TEST_LAST_FILE_JSON = 'files/post_last_page.json'

EXPECTED_CURSOR_1 = ('AQHR3Q0F0zB5OZDu_aGVCZScdABOl9BRwJJxZdHNaEVcsGEhXcMnLBzwQMIn3rWLmzH-7a5Yaer'
                     '_GWpH6dWPvMe8enPGl_TEK2XValXV1ilzXAGPkbndRVrF8iYESzdB-cT8osR2ORE7d3FOlfQAwS'
                     'Uisb2udmuq9YmiW5lNzpSv0Qmw9ti12MVch0sscPHPdvCrYcHRaDCbxGKuromYmHeN6SAMW3WqX'
                     'JLiVMAyDrqirAX8Lr3lmUfZ6zrUseF1mcCbBDTs6yszf-1KUzjaxdjKdDHrcd7KeRkNCMBbPEeU'
                     'qdhybxpWgtfqhJRGaaYZP44jKFK6mN0O7DOsj273e2V1A2EDt7PqWXVdIsM54QIf0pfaSVwsYL1'
                     '88_TzEMnHfLtr8E5EHP_1_3dIryKsydUa_DjDJUJdU9LoJw9AnDBJwAmqlm-rL_gP0mPBn8rB0a'
                     '5_rstMfLKcc3It8EmJDtkTQg')

EXPECTED_CURSOR_2 = ('AQHREMORimDahq91xO9oLIrK7v992dRV7SHVgk2Oiwhw_TMVJT2GEfJsJckcay4djGOWjxilvhJx'
                     '0zfPVwebO5yidWfuzQEB5gUegcTagMyCekgBLJLOO3qAdcalKY4m8BhWS2a4JBnxTftxVH_eXCpo'
                     'RSvRHlyNbLqQgwEvP7sGwgiMRfmfZ8PuMbTLyDmuPoeeKSWwyTn4z72QDTOG7sS5qpawWiCPA_Tv'
                     'zv9QZpJekJvHFrweJxOtenkg2g_3PJAsDATkLOYySf3vW_33IKKfcIBbmx4dRT8AsjYHOe1-_p08'
                     'uj_nNKzaY7bw014SxP1l54Xugc80gdbVt18QpDOJDppwgXivPkhOjLsc1ZbhW4vIN836C8ftzfN8'
                     'aKRwQQKVwR7N1o83R_Iqbcg0GlJdMmwOBvyk7WYPU1jmr1bFQjCYUDeeAep_gBYLK5vwO2p8TCpL'
                     '2gW52JEKu3feLfDK2w')


class TestPostExtractor(unittest.TestCase):

    def setUp(self):
        self.spp = PostSummaryListExtractor()
        self.html_content_1 = read_test_file(POST_TEST_FIRST_FILE_HTML)
        self.html_content_2 = read_test_file(POST_TEST_SECOND_FILE_HTML)
        self.html_content_3 = read_test_file(POST_TEST_LAST_FILE_HTML)

        self.exp_1 = _load_expected_posts(Path(POST_TEST_FIRST_FILE_JSON))
        self.exp_2 = _load_expected_posts(Path(POST_TEST_SECOND_FILE_JSON))
        self.exp_3 = _load_expected_posts(Path(POST_TEST_LAST_FILE_JSON))

    def test_extract_first_page(self):
        self._extract_page(self.html_content_1, EXPECTED_CURSOR_1, self.exp_1)

    def test_extract_second_page(self):
        self._extract_page(self.html_content_2, EXPECTED_CURSOR_2, self.exp_2)

    def test_extract_last_page(self):
        self._extract_page(self.html_content_3, '', self.exp_3)

    def _extract_page(self, text: str, expected_cursor: str, expected_posts: List) -> None:
        res: PostList = self.spp.extract_posts(text)
        self.assertIsInstance(res.posts, list)
        self.assertEqual(res.cursor, expected_cursor)
        # TO GET JSON: items_json = json.dumps(res.posts, default=pydantic_encoder, indent=4)
        self.assertEqual(len(res.posts), len(expected_posts))
        for i in range(len(res.posts)):
            found = False
            for j in range(len(expected_posts)):
                if res.posts[i].id == expected_posts[j].id:
                    self.assertEqual(res.posts[i], expected_posts[j])
                    found = True
                    break
            self.assertTrue(found, f"Post with id {res.posts[i].id} not found in expected posts")


class TestPostSummary(unittest.TestCase):

    def setUp(self):
        self.first_page_html = read_test_file(POST_TEST_FIRST_FILE_HTML)
        self.second_page_html = read_test_file(POST_TEST_SECOND_FILE_HTML)
        self.exp_1 = _load_expected_posts(Path(POST_TEST_FIRST_FILE_JSON))
        self.exp_2 = _load_expected_posts(Path(POST_TEST_SECOND_FILE_JSON))

    def test_extract_post_id(self):
        req = MockRequester()
        req.add_expected_response(
            r_text=self.first_page_html
        )
        req.add_expected_response(
            r_text=self.second_page_html
        )
        opts = GetPostOptions(
            requester=req,
            parser=PostSummaryListExtractor(),
            sleep_time_max=0,
            sleep_time_min=0
        )
        repo = PostSummaryListRepository(opts)
        gen = repo.get_posts('username', [StopAfterNPosts(10)])
        total_exp = self.exp_1 + self.exp_2
        post_list = list(gen)
        for i in range(len(post_list)):
            found = False
            for j in range(len(total_exp)):
                if post_list[i].id == total_exp[j].id:
                    self.assertEqual(post_list[i], total_exp[j])
                    found = True
                    break
            self.assertTrue(found, f"Post with id {post_list[i].id} not found in expected posts")
