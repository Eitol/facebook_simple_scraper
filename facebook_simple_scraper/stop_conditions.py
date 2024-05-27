import time
from typing import List

from facebook_simple_scraper.entities import Post, StopCondition


class StopAfterNPosts(StopCondition):
    """Stop condition that stops scraping after a specified number of posts."""

    def __init__(self, n: int):
        """
        Args:
            n (int): The number of posts after which to stop scraping.
        """
        self.n = n

    def should_stop(self, post_list: List[Post]) -> bool:
        """Check if the number of posts scraped has reached the limit.

        Args:
            post_list (List[Post]): The list of posts scraped so far.

        Returns:
            bool: True if the number of posts is greater than or equal to n, False otherwise.
        """
        return len(post_list) >= self.n


class StopAfterNComments(StopCondition):
    """Stop condition that stops scraping after a specified number of comments."""

    def __init__(self, n: int):
        """
        Args:
            n (int): The number of comments after which to stop scraping.
        """
        self.n = n

    def should_stop(self, post_list: List[Post]) -> bool:
        """Check if the total number of comments scraped has reached the limit.

        Args:
            post_list (List[Post]): The list of posts scraped so far.

        Returns:
            bool: True if the number of comments is greater than or equal to n, False otherwise.
        """
        return sum([len(p.comments) for p in post_list]) >= self.n


class StopAfterNSeconds(StopCondition):
    """Stop condition that stops scraping after a specified number of seconds."""

    def __init__(self, n_secs: int):
        """
        Args:
            n_secs (int): The number of seconds after which to stop scraping.
        """
        self.start_time = time.time()
        self.n_secs = n_secs

    def should_stop(self, post_list: List[Post]) -> bool:
        """Check if the elapsed time has reached the limit.

        Args:
            post_list (List[Post]): The list of posts scraped so far.

        Returns:
            bool: True if the elapsed time is greater than or equal to n_secs, False otherwise.
        """
        return (time.time() - self.start_time) >= self.n_secs


class StopAfterPostId(StopCondition):
    """Stop condition that stops scraping after a specific post ID is encountered."""

    def __init__(self, post_id: str):
        """
        Args:
            post_id (str): The post ID after which to stop scraping.
        """
        self.post_id = post_id

    def should_stop(self, post_list: List[Post]) -> bool:
        """Check if the specified post ID is in the list of posts scraped.

        Args:
            post_list (List[Post]): The list of posts scraped so far.

        Returns:
            bool: True if the post ID is found in the post list, False otherwise.
        """
        return self.post_id in [p.id for p in post_list]
