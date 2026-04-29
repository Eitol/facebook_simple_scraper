from dataclasses import dataclass, field
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
        location: Optional Facebook location vanity slug (e.g. ``miami``,
            ``buenos-aires``). Only some cities have a vanity slug; for
            arbitrary locations use ``latitude``/``longitude``/``radius_km``
            instead. If neither is provided, Facebook falls back to the
            location detected from the request IP.
        latitude: Latitude of the search center (decimal degrees).
        longitude: Longitude of the search center (decimal degrees).
        radius_km: Search radius in kilometers (defaults to 65, FB default).
        condition: Whether to look for ``NEW``, ``USED`` or ``ALL`` vehicles.
        query: Optional free-text search (e.g. ``toyota corolla``).
        min_price: Optional minimum price filter.
        max_price: Optional maximum price filter.
        availability: Whether to look for listings that are still
            available (``IN_STOCK``), already sold/pending
            (``OUT_OF_STOCK``) or both (``ALL``, default).
        days_since_listed: Restrict results to listings posted within
            the last day / week / month. ``ANY`` (default) does not
            restrict by date.
        category_id: Marketplace category id. Defaults to the generic
            "Vehicles" category. Only override if you know what you are
            doing (e.g. to scope to motorcycles, RVs, etc).

    Note:
        Facebook only honors ``latitude``/``longitude`` (and most other
        filters) for **logged-in** sessions. Unauthenticated requests
        always use the IP-based location.
    """

    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_km: int = 65
    condition: VehicleCondition = VehicleCondition.ALL
    query: Optional[str] = None
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    availability: VehicleAvailability = VehicleAvailability.ALL
    days_since_listed: DaysSinceListed = DaysSinceListed.ANY
    category_id: str = "807311116002614"


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
    is_sold: Optional[bool] = None
    is_pending: Optional[bool] = None
    raw: Optional[dict] = None


class MarketplaceVehicleList(BaseModel):
    """A page of vehicle listings + the cursor to fetch the next page."""

    listings: List[MarketplaceVehicleListing]
    cursor: Optional[str] = None


@dataclass
class MarketplaceListingDetail:
    """Full detail for a single Facebook Marketplace listing.

    Obtained by fetching ``/marketplace/item/<id>/`` and extracting the
    embedded JSON. Includes all photos, the visible description text, and
    any vehicle-specific attributes exposed by Facebook.
    """

    id: str
    url: str
    title: Optional[str]
    price: Optional[str]
    price_amount: Optional[float]
    currency: Optional[str]
    description: Optional[str]
    location: Optional[str]
    images: List[str]
    seller_name: Optional[str]
    creation_time: Optional[datetime]
    is_sold: Optional[bool]
    is_pending: Optional[bool]
    mileage: Optional[str]
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_condition: Optional[str] = None
    vehicle_transmission: Optional[str] = None
    vehicle_fuel_type: Optional[str] = None
    vehicle_exterior_color: Optional[str] = None
    raw: Optional[dict] = None
