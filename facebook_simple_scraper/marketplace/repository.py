import os
import time
from dataclasses import dataclass
from random import randint
from typing import Iterable, List, Optional
from urllib.parse import urlencode

from facebook_simple_scraper.entities import StopCondition
from facebook_simple_scraper.marketplace.entities import (
    DaysSinceListed,
    MarketplaceListingDetail,
    MarketplaceVehicleFilters,
    MarketplaceVehicleListing,
    VehicleAvailability,
    VehicleCondition,
)
from facebook_simple_scraper.marketplace.extractor import (
    MarketplaceDetailExtractor,
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


def _price_in_range(
    price_amount: Optional[float], filters: MarketplaceVehicleFilters
) -> bool:
    """Return True if *price_amount* satisfies the min/max filters.

    When either ``min_price`` or ``max_price`` is set, listings whose price
    could not be determined are dropped (treated as out-of-range). When no
    price bounds are set, every listing passes through.
    """
    has_bounds = filters.min_price is not None or filters.max_price is not None
    if not has_bounds:
        return True
    if price_amount is None:
        return False
    if filters.min_price is not None and price_amount < filters.min_price:
        return False
    if filters.max_price is not None and price_amount > filters.max_price:
        return False
    return True


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
        debug = os.environ.get("FB_MARKETPLACE_DEBUG") == "1"
        debug_raw = os.environ.get("FB_MARKETPLACE_DEBUG_RAW") == "1"

        while True:
            url = self._build_url(filters, cursor=self._cursor)
            if debug:
                print(f"[fb-marketplace] GET {url}")
            response = self._requester.request("GET", url)
            page = self._parser.extract(response.text)
            self._cursor = page.cursor
            if debug:
                print(
                    f"[fb-marketplace] extracted {len(page.listings)} listings "
                    f"(filter min={filters.min_price} max={filters.max_price})"
                )

            for listing in page.listings:
                if listing.id in seen_ids:
                    continue
                seen_ids.add(listing.id)
                if not _price_in_range(listing.price_amount, filters):
                    if debug:
                        print(
                            f"[fb-marketplace] DROP price={listing.price_amount!r} "
                            f"str={listing.price!r} id={listing.id} "
                            f"title={listing.title[:60]!r}"
                        )
                    continue
                if debug:
                    print(
                        f"[fb-marketplace] KEEP price={listing.price_amount!r} "
                        f"str={listing.price!r} id={listing.id} "
                        f"title={listing.title[:60]!r}"
                    )
                if debug_raw and listing.raw is not None:
                    import json as _json
                    print("[fb-marketplace] RAW:", _json.dumps(listing.raw, default=str)[:2000])
                accumulated.append(listing)
                yield listing

            if not self._cursor:
                return
            for cond in stop_conditions:
                if cond.should_stop(accumulated):
                    return
            self._sleep()

    def get_detail(self, listing_id: str) -> Optional[MarketplaceListingDetail]:
        """Fetch and parse the detail page for a single listing.

        Args:
            listing_id: The numeric Facebook Marketplace listing ID (e.g.
                ``"1257546456545056"``).

        Returns:
            A :class:`MarketplaceListingDetail` if data could be extracted,
            ``None`` otherwise.
        """
        url = f"https://www.facebook.com/marketplace/item/{listing_id}/"
        response = self._requester.request("GET", url)
        extractor = MarketplaceDetailExtractor()
        return extractor.extract(response.text, listing_id)

    def get_cursor(self) -> Optional[str]:
        return self._cursor

    # -------- helpers ---------------------------------------------------

    @staticmethod
    def _build_url(
        filters: MarketplaceVehicleFilters, cursor: Optional[str] = None
    ) -> str:
        params: List[tuple] = [("category_id", filters.category_id)]

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
        if filters.availability == VehicleAvailability.IN_STOCK:
            params.append(("availability", "in stock"))
        elif filters.availability == VehicleAvailability.OUT_OF_STOCK:
            params.append(("availability", "out of stock"))
        if filters.days_since_listed and filters.days_since_listed != DaysSinceListed.ANY:
            params.append(("daysSinceListed", str(int(filters.days_since_listed))))
        if filters.latitude is not None and filters.longitude is not None:
            params.append(("latitude", str(filters.latitude)))
            params.append(("longitude", str(filters.longitude)))
            params.append(("radius", str(filters.radius_km)))
        if cursor:
            params.append(("cursor", cursor))
        params.append(("exact", "false"))

        qs = urlencode(params)
        slug = (filters.location or "").strip("/ ")
        if slug:
            # Keep the vanity-URL form when a slug is provided, otherwise
            # use the generic search endpoint scoped via lat/lng (or the
            # IP-derived default location for unauthenticated requests).
            return f"https://www.facebook.com/marketplace/{slug}/search/?{qs}"
        return f"https://www.facebook.com/marketplace/category/search/?{qs}"

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
