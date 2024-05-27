import abc
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, HttpUrl

from facebook_simple_scraper.default_values import DEFAULT_MAX_COMMENTS_PER_POST, DEFAULT_SLEEP_TIME_MAX, \
    DEFAULT_SLEEP_TIME_MIN
from facebook_simple_scraper.requester import requester


class MediaQuality(Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'


class Image(BaseModel):
    id: str
    url: HttpUrl
    description: str
    quality: MediaQuality


class User(BaseModel):
    id: str
    name: str
    gender: str
    photo: str


class ReactionType(Enum):
    UNKNOWN = 'UNKNOWN'
    LIKE = 'LIKE'
    CARE = 'CARE'
    WOW = 'WOW'
    ANGRY = 'ANGRY'
    LOVE = 'LOVE'
    HAHA = 'HAHA'
    SAD = 'SAD'


class Reaction(BaseModel):
    type: ReactionType
    count: int


class Comment(BaseModel):
    id: str
    text: str
    date: datetime
    user: User
    url: str
    replies: List['Comment']
    reactions: List[Reaction]
    replies_count: int


class Video(BaseModel):
    id: str
    url: HttpUrl
    description: str
    quality: MediaQuality
    duration: int
    height: int
    width: int
    size: int
    thumbnail: HttpUrl
    watches: int


class LoginCredentials(BaseModel):
    username: str
    password: str


class SessionStorage(abc.ABC):
    @abc.abstractmethod
    def get_requester(self, username: str) -> requester.Requester:
        raise NotImplementedError()

    @abc.abstractmethod
    def save_requester(self, username: str, session: requester.Requester) -> None:
        raise NotImplementedError()


class Post(BaseModel):
    id: str
    url: str
    text: str
    date: datetime
    image_url: str
    video_url: str
    like_count: int
    comment_count: int
    comments: List[Comment] = []


class PostList(BaseModel):
    posts: List[Post]
    cursor: str
    profile_id: str


class ScrapingCallbacks:

    def on_get_post_start(self, post_url: HttpUrl) -> None:
        pass

    def on_get_post_end(self, post: Post) -> None:
        pass

    def on_get_comments_start(self, post: Post) -> None:
        pass

    def on_get_comments_end(self, post: Post) -> None:
        pass


class UserInfo(BaseModel):
    username: str
    profile_name: str
    target: str
    fb_dtsg: str


class StopCondition:
    """Base class for defining stop conditions for the scraper."""

    def should_stop(self, post_list: List[Post]) -> bool:
        """Determine whether the scraping should stop.

        Args:
            post_list (List[Post]): The list of posts scraped so far.

        Returns:
            bool: True if the scraping should stop, False otherwise.
        """
        raise NotImplementedError


@dataclass
class ScraperOptions:
    """Class to hold configuration options for the scraper."""

    credentials: List[LoginCredentials]
    """List of login credentials to be used by the scraper."""

    session_storage: Optional[SessionStorage] = None
    """Optional session storage to persist sessions. Defaults to None."""

    callbacks: ScrapingCallbacks = ScrapingCallbacks()
    """Callbacks to handle various events during scraping. Defaults to an instance of ScrapingCallbacks."""

    sleep_time_min: int = DEFAULT_SLEEP_TIME_MIN
    """Minimum sleep time (in seconds) between scraping actions. Defaults to DEFAULT_SLEEP_TIME_MIN."""

    sleep_time_max: int = DEFAULT_SLEEP_TIME_MAX
    """Maximum sleep time (in seconds) between scraping actions. Defaults to DEFAULT_SLEEP_TIME_MAX."""

    stop_conditions: Optional[List[StopCondition]] = None
    """List of conditions that will cause the scraper to stop. Defaults to None."""

    max_comments_per_post: int = DEFAULT_MAX_COMMENTS_PER_POST
    """Maximum number of comments to scrape per post. Defaults to DEFAULT_MAX_COMMENTS_PER_POST."""
