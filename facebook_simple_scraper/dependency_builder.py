from typing import Tuple, Optional

from facebook_simple_scraper.comments.repository import GraphqlCommentsRepository
from facebook_simple_scraper.default_values import DEFAULT_SESSION_DIR
from facebook_simple_scraper.entities import ScraperOptions, SessionStorage
from facebook_simple_scraper.login.login import MobileBasicLoginRepository
from facebook_simple_scraper.login.params import MbasicLoginParamsRepository
from facebook_simple_scraper.login.session_storage import LocalFileSessionStorage
from facebook_simple_scraper.posts.summary_extractor import PostSummaryListExtractor
from facebook_simple_scraper.posts.summary_repository import PostSummaryListRepository, GetPostOptions
from facebook_simple_scraper.requester import requester


class AbstractScraperDependencyBuilder:
    """Abstract class for building dependencies for a web scraper."""

    @staticmethod
    def build_deps(opts: ScraperOptions) -> Tuple[MobileBasicLoginRepository, PostSummaryListRepository]:
        """Build dependencies required for the scraper. """
        raise NotImplementedError()


class DefaultScraperDependencyBuilder:
    """
    Default implementation of AbstractScraperDependencyBuilder.

    You can extend this class to create a custom implementation.
    For example you can:
        - Change session storage so that it stores the session in a database instead of a file.
        - Change the requester to use a proxy.
    """

    @staticmethod
    def build_deps(opts: ScraperOptions) -> Tuple[MobileBasicLoginRepository, PostSummaryListRepository]:
        """Build the default dependencies for the scraper.

        Args:
            opts (ScraperOptions): The options/configuration for the scraper.

        Returns:
            Tuple[MobileBasicLoginRepository, PostSummaryListRepository]: A tuple
            containing the login repository and post summary repository.
        """

        # Create a requester for Facebook sessions
        req = requester.FacebookSessionBasedRequester()

        # Create a repository for login parameters
        params_repo = MbasicLoginParamsRepository(req)

        session_storage: Optional[SessionStorage] = None
        # Determine session storage mechanism
        if opts.session_storage is None:
            session_storage = LocalFileSessionStorage(DEFAULT_SESSION_DIR)
        else:
            session_storage = opts.session_storage

        # Initialize the login repository with the necessary dependencies
        login_repo = MobileBasicLoginRepository(
            params_repo,
            session_storage=session_storage,
            requester=req,
        )

        # Initialize the comments repository
        comment_repo = GraphqlCommentsRepository(req)

        # Initialize the post summary list extractor and options
        post_extractor = PostSummaryListExtractor()
        post_opts = GetPostOptions(
            requester=req,
            parser=post_extractor,
            sleep_time_min=opts.sleep_time_min,
            sleep_time_max=opts.sleep_time_max,
            comments_repository=comment_repo,
        )

        # Initialize the post summary list repository
        post_repo = PostSummaryListRepository(post_opts)

        # Return the login and post repositories
        return login_repo, post_repo
