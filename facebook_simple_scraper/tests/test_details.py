import json
import unittest
from typing import List

from facebook_simple_scraper.details.extractor import GQLPostDetailExtractor
from facebook_simple_scraper.entities import Comment, ReactionType
from facebook_simple_scraper.tests.utils import read_test_file

PAGE_1 = '../tests/files/get_comments_gql_page_1.jsonlines'
PAGE_1_W_REACTIONS = '../tests/files/get_comments_and_reactions.jsonlines'
EXPECTED_PAGE_1 = '../tests/files/get_comments_gql_page_1_expected.json'
EXPECTED_CURSOR_1 = 'AQHRjbwVYWY_CphyGACRGLHX6TF7WCSuAQHqScDVYMRZQUXHGB1Vp2go5DXevusrbp6VBsXt3qFsjxwd7a_nW1tg1g'


def _load_expected_comments(file_path: str) -> List[Comment]:
    expected_result_json = json.loads(read_test_file(file_path))
    expected: List[Comment] = []
    for expected_post_dict in expected_result_json:
        expected.append(Comment(**expected_post_dict))
    return expected


class TestReactionsExtractor(unittest.TestCase):
    def test_extract_reactions(self):
        self.gql_extractor = GQLPostDetailExtractor()
        json_content = read_test_file(PAGE_1_W_REACTIONS)
        detail = self.gql_extractor.extract(json_content)
        self.assertEqual(len(detail.reactions), 6)
        self.assertEqual(detail.reactions[0].type, ReactionType.LIKE)
        self.assertEqual(detail.reactions[0].count, 89)
        self.assertEqual(detail.reactions[1].type, ReactionType.LOVE)
        self.assertEqual(detail.reactions[1].count, 40)
        self.assertEqual(detail.reactions[2].type, ReactionType.WOW)
        self.assertEqual(detail.reactions[2].count, 9)


class TestCommentsExtractor(unittest.TestCase):

    def setUp(self):
        self.gql_extractor = GQLPostDetailExtractor()
        self.json_content_1 = read_test_file(PAGE_1)
        self.json_content_1 = read_test_file(PAGE_1)
        self.exp_comments_1 = _load_expected_comments(EXPECTED_PAGE_1)
        self.exp_cursor_1 = EXPECTED_CURSOR_1

    def test_extract_first_page(self):
        self._extract_page(self.json_content_1, self.exp_cursor_1, self.exp_comments_1)

    def _extract_page(self, text: str, expected_cursor: str, expected_comments: List[Comment]) -> None:
        detail = self.gql_extractor.extract(text)
        # items_json = json.dumps(comments, default=pydantic_encoder, indent=4)
        self.assertEqual(detail.next_cursor, expected_cursor)
        self.assertEqual(len(detail.comments), len(expected_comments))
        self._compare_comments(detail.comments, expected_comments)

    def _compare_comments(self, comments: List[Comment], expected_comments: List[Comment]) -> None:
        if len(comments) != len(expected_comments):
            self.fail(f"Expected {len(expected_comments)} comments, got {len(comments)}")
        for comment_idx in range(len(comments)):
            comment_found = False
            for j in range(len(expected_comments)):
                if comments[comment_idx].id == expected_comments[j].id:
                    self.assertEqual(comments[comment_idx], expected_comments[j])
                    comment_found = True
                    break
            self.assertTrue(comment_found, f"Post with id {comments[comment_idx].id} not found in expected posts")
