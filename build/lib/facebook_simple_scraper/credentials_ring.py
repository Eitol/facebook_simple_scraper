from typing import List, Iterable

from facebook_simple_scraper.entities import LoginCredentials


class CredentialsRingBuffer:
    def __init__(self, creds: List[LoginCredentials]):
        self.index = 0
        self.creds = creds

    def append(self, datum):
        self.creds.append(datum)

    def next(self) -> Iterable[LoginCredentials]:
        if self.index >= len(self.creds):
            self.index = 0
        cred = self.creds[self.index]
        self.index += 1
        yield cred
