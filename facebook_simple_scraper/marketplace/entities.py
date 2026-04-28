from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class VehicleCondition(str, Enum):
    """Filter for the condition of vehicles to search for in Marketplace."""

    NEW = "NEW"
    USED = "USED"
    ALL = "ALL"


class VehicleAvailability(str, Enum):
    """Filter for the availability of the listing.

    Mirrors the ``availability`` query parameter Facebook uses on
    Marketplace search URLs (``in stock`` / ``out of stock``).
    ``ALL`` means do not constrain availability.
    """

    IN_STOCK = "IN_STOCK"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    ALL = "ALL"


class DaysSinceListed(int, Enum):
    """Filter for how recently the listing was published.

    Facebook Marketplace only exposes the values 1, 7 and 30 in its UI
    for the ``daysSinceListed`` query parameter. ``ANY`` means do not
    constrain the date.
    """

    LAST_DAY = 1
    LAST_WEEK = 7
    LAST_MONTH = 30
    ANY = 0


class MarketplaceVehicleFilters(BaseModel):
    """Filters used to search vehicle listings in Facebook Marketplace.

    Attributes:
        location: Facebook location slug (e.g. ``santiago``,
            ``buenos-aires``, ``miami``). Required, since Marketplace
            results are scoped to a location.
        condition: Whether to look for ``NEW``, ``USED`` or ``ALL`` vehicles.
        query: Optional free-text search (e.g. ``toyota corolla``).
        min_price: Optional minimum price filter.
        max_price: Optional maximum price filter.
        availability: Whether to look for listings that are still
            available (``IN_STOCK``), already sold (``OUT_OF_STOCK``)
            or both (``ALL``, default).
        days_since_listed: Restrict results to listings posted within
            the last day / week / month. ``ANY`` (default) does not
            restrict by date.
    """

    location: str
    condition: VehicleCondition = VehicleCondition.ALL
    query: Optional[str] = None
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    availability: VehicleAvailability = VehicleAvailability.ALL
    days_since_listed: DaysSinceListed = DaysSinceListed.ANY


class MarketplaceVehicleListing(BaseModel):
    """A single vehicle listing extracted from Facebook Marketplace."""

    id: str
    url: str
    title: str
    price: Optional[str] = None
    price_amount: Optional[float] = None
    currency: Optional[str] = None
    location: Optional[str] = None
    image_url: Optional[str] = None
    seller_name: Optional[str] = None
    creation_time: Optional[datetime] = None
    mileage: Optional[str] = None
    is_new: Optional[bool] = None
    raw: Optional[dict] = None


class MarketplaceVehicleList(BaseModel):
    """A page of vehicle listings + the cursor to fetch the next page."""

    listings: List[MarketplaceVehicleListing]
    cursor: Optional[str] = None
