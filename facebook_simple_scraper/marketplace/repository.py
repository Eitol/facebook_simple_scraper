import time
from dataclasses import dataclass
from random import randint
from typing import Iterable, List, Optional
from urllib.parse import urlencode

from facebook_simple_scraper.entities import StopCondition
from facebook_simple_scraper.marketplace.entities import (
    MarketplaceVehicleFilters,
    MarketplaceVehicleListing,
    VehicleCondition,
)
from facebook_simple_scraper.marketplace.extractor import (
    MarketplaceListingsExtractor,
    MarketplaceListingsParser,
)
from facebook_simple_scraper.requester.requester import Requester


@dataclass
class GetMarketplaceVehiclesOptions:
    requester: Requester
    parser: MarketplaceListingsParser
    sleep_time_min: int = 5
    sleep_time_max: int = 10


class MarketplaceVehicleRepository:
    """Repository that searches vehicle listings on Facebook Marketplace."""

    def __init__(self, opts: GetMarketplaceVehiclesOptions):
        self._requester = opts.requester
        self._parser = opts.parser
        self._sleep_time_min = opts.sleep_time_min
        self._sleep_time_max = opts.sleep_time_max
        self._cursor: Optional[str] = None

    def search(
        self,
        filters: MarketplaceVehicleFilters,
        stop_conditions: Optional[List[StopCondition]] = None,
    ) -> Iterable[MarketplaceVehicleListing]:
        """Yield vehicle listings matching ``filters``.

        Pagination is handled automatically using the ``end_cursor`` returned
        by Facebook. Iteration stops when no further cursor is found or any
        of the supplied ``stop_conditions`` returns True.
        """
        stop_conditions = stop_conditions or []
        seen_ids: set = set()
        accumulated: List = []
        self._cursor = None

        while True:
            url = self._build_url(filters, cursor=self._cursor)
            response = self._requester.request("GET", url)
            page = self._parser.extract(response.text)
            self._cursor = page.cursor

            for listing in page.listings:
                if listing.id in seen_ids:
                    continue
                seen_ids.add(listing.id)
                accumulated.append(listing)
                yield listing

            if not self._cursor:
                return
            for cond in stop_conditions:
                if cond.should_stop(accumulated):
                    return
            self._sleep()

    def get_cursor(self) -> Optional[str]:
        return self._cursor

    # -------- helpers ---------------------------------------------------

    @staticmethod
    def _build_url(
        filters: MarketplaceVehicleFilters, cursor: Optional[str] = None
    ) -> str:
        location = (filters.location or "").strip("/ ")
        if not location:
            raise ValueError("MarketplaceVehicleFilters.location is required")

        params: List[tuple] = []
        if filters.query:
            params.append(("query", filters.query))
        if filters.condition == VehicleCondition.NEW:
            params.append(("itemCondition", "NEW"))
        elif filters.condition == VehicleCondition.USED:
            # Facebook groups the various used conditions under these codes.
            params.append(("itemCondition", "USED_LIKE_NEW,USED_GOOD,USED_FAIR"))
        if filters.min_price is not None:
            params.append(("minPrice", str(filters.min_price)))
        if filters.max_price is not None:
            params.append(("maxPrice", str(filters.max_price)))
        if cursor:
            params.append(("cursor", cursor))
        params.append(("exact", "false"))

        qs = urlencode(params)
        return (
            f"https://www.facebook.com/marketplace/{location}/vehicles/?{qs}"
        )

    def _sleep(self) -> None:
        if self._sleep_time_max <= 0:
            return
        time.sleep(randint(self._sleep_time_min, self._sleep_time_max))


def build_default_marketplace_repository(
    requester: Requester,
    sleep_time_min: int = 5,
    sleep_time_max: int = 10,
) -> MarketplaceVehicleRepository:
    return MarketplaceVehicleRepository(
        GetMarketplaceVehiclesOptions(
            requester=requester,
            parser=MarketplaceListingsExtractor(),
            sleep_time_min=sleep_time_min,
            sleep_time_max=sleep_time_max,
        )
    )
