from datetime import datetime
from typing import Optional


class SessionExpiredError(Exception):
    def __init__(self, expiration_date: Optional[datetime]):
        super().__init__(f"The 'datr' cookie has expired on {expiration_date}")


class SessionNotFoundError(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class CheckpointRequiredException(Exception):

    def __init__(self, msg: str):
        super().__init__(f"Checkpoint required. {msg}")


class LoginFailedException(Exception):

    def __init__(self, msg: str):
        super().__init__(f"Login failed for user. {msg}")


class ApiError(Exception):

    def __init__(self, msg: str):
        super().__init__(f"API error: {msg}")
