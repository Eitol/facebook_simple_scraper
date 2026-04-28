from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class VehicleCondition(str, Enum):
    """Filter for the condition of vehicles to search for in Marketplace."""

    NEW = "NEW"
    USED = "USED"
    ALL = "ALL"


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
    """

    location: str
    condition: VehicleCondition = VehicleCondition.ALL
    query: Optional[str] = None
    min_price: Optional[int] = None
    max_price: Optional[int] = None


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
