import abc
from dataclasses import dataclass
from typing import Optional

from facebook_simple_scraper.entities import UserInfo
from facebook_simple_scraper.requester.requester import Requester


@dataclass
class LoginParams:
    jazoest: Optional[str] = None
    lsd: Optional[str] = None
    li: Optional[str] = None
    fb_dtsg: Optional[str] = None
    target: Optional[str] = None


class LoginParamsRepository(abc.ABC):

    @abc.abstractmethod
    def get_login_params(self) -> LoginParams:
        raise NotImplementedError()

    @abc.abstractmethod
    def extract_params_from_html(self, fb_html_login_page: str) -> LoginParams:
        raise NotImplementedError()


@dataclass
class LoginResponse:
    was_logged: bool
    save_device: bool
    user_info: Optional[UserInfo] = None
    requester: Optional[Requester] = None
    fb_dtsg: Optional[str] = None


class LoginRepository(abc.ABC):

    @abc.abstractmethod
    def login(self, user: str, password: str) -> LoginResponse:
        raise NotImplementedError()
