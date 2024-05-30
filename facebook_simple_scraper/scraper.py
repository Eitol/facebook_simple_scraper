from typing import Optional, Iterable

from facebook_simple_scraper.credentials_ring import CredentialsRingBuffer
from facebook_simple_scraper.dependency_builder import AbstractScraperDependencyBuilder, DefaultScraperDependencyBuilder
from facebook_simple_scraper.details.extractor import PostDetails
from facebook_simple_scraper.entities import ScraperOptions, Post
from facebook_simple_scraper.posts.summary_repository import PostSummaryListRepository


class Scraper:
    """Main scraper class responsible for scraping posts from an account."""

    def __init__(self, opts: ScraperOptions, deps_builder: Optional[AbstractScraperDependencyBuilder] = None):
        """Initialize the scraper with options and dependencies builder.

        Args:
            opts (ScraperOptions): The options/configuration for the scraper.
            deps_builder (AbstractScraperDependencyBuilder, optional): Defaults to DefaultScraperDependencyBuilder.

        Raises:
            ValueError: If required options such as credentials or stop conditions are missing.
        """
        self.opts = opts

        # Use default dependency builder if none is provided
        if deps_builder is None:
            self.deps_builder = DefaultScraperDependencyBuilder()

        # Validate credentials
        if opts.credentials is None:
            raise ValueError("Credentials are required")
        if len(opts.credentials) == 0:
            raise ValueError("At least one credential is required")

        # Validate stop conditions
        if opts.stop_conditions in [None, []]:
            raise ValueError("Stop conditions are required")

        # Initialize credential handling
        self.current_credential_index = 0
        self.creds_ring = CredentialsRingBuffer(opts.credentials)
        self.post_repo: Optional[PostSummaryListRepository] = None

    def get_posts(self, account_ids: str) -> Iterable[Post]:
        """Scrape posts from the given account IDs.

        Args:
            account_ids (str): The IDs of the accounts to scrape posts from.

        Yields:
            Iterable[Post]: A generator yielding posts.
        """
        # Build the necessary dependencies
        login_repo, post_repo = self.deps_builder.build_deps(self.opts)

        # Iterate through the credentials in a ring buffer fashion
        for cred in self.creds_ring.next():
            # Login using the current credential
            login_resp = login_repo.login(cred.username, cred.password)
            login_repo, post_repo = self.deps_builder.build_deps(self.opts, req=login_resp.requester)
            self.post_repo = post_repo
            # Get posts using the post repository and stop conditions
            gen = post_repo.get_posts(account_ids, self.opts.stop_conditions)

            # Yield each post
            for post in gen:
                yield post

    def get_post_details(self, post_id: str) -> PostDetails:
        if self.post_repo is None:
            raise ValueError("Post repository is not initialized")
        return self.post_repo.get_post_details(post_id)

    def get_latest_cursor(self) -> Optional[str]:
        if self.post_repo is None:
            raise ValueError("Post repository is not initialized")
        return self.post_repo.get_cursor()
