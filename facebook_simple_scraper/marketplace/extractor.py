"""Extract vehicle listings from a Facebook Marketplace HTML response.

Facebook embeds the data of the listings inside ``<script>`` tags as JSON
(payloads of ``handleWithCustomApplyEach`` / ``RelayPrefetchedStreamCache``
calls). The HTML itself is rendered later by React, so a plain BeautifulSoup
extraction over the rendered DOM is unreliable. Instead, we walk every
``<script>`` block, try to parse JSON fragments out of it, and recursively
look for objects that look like a Marketplace listing
(``__typename == "MarketplaceListing"``).
"""
import abc
import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from bs4 import BeautifulSoup

from facebook_simple_scraper.marketplace.entities import (
    MarketplaceVehicleList,
    MarketplaceVehicleListing,
)


_LISTING_TYPENAMES = {"MarketplaceListing", "GroupCommerceProductItem"}


class MarketplaceListingsParser(abc.ABC):
    @abc.abstractmethod
    def extract(self, html_content: str) -> MarketplaceVehicleList:
        raise NotImplementedError()


class MarketplaceListingsExtractor(MarketplaceListingsParser):
    """Extracts vehicle listings + pagination cursor from raw HTML."""

    def extract(self, html_content: str) -> MarketplaceVehicleList:
        listings: List[MarketplaceVehicleListing] = []
        cursor: Optional[str] = None
        seen_ids: set = set()

        for obj in self._iter_json_objects(html_content):
            for node in _walk(obj):
                if not isinstance(node, dict):
                    continue
                typename = node.get("__typename")
                if typename in _LISTING_TYPENAMES:
                    listing = self._parse_listing(node)
                    if listing is None:
                        continue
                    if listing.id in seen_ids:
                        continue
                    seen_ids.add(listing.id)
                    listings.append(listing)
                page_info = node.get("page_info")
                if isinstance(page_info, dict):
                    end_cursor = page_info.get("end_cursor")
                    if end_cursor and not cursor:
                        cursor = end_cursor

        return MarketplaceVehicleList(listings=listings, cursor=cursor)

    # ----- listing parsing ----------------------------------------------

    @staticmethod
    def _parse_listing(node: Dict[str, Any]) -> Optional[MarketplaceVehicleListing]:
        listing_id = node.get("id") or node.get("legacy_id") or node.get("story_id")
        if not listing_id:
            return None
        listing_id = str(listing_id)

        title = (
            node.get("marketplace_listing_title")
            or node.get("custom_title")
            or node.get("name")
            or ""
        )
        if not title:
            return None

        price_node = (
            node.get("listing_price")
            or node.get("formatted_price")
            or node.get("price")
            or {}
        )
        price_str: Optional[str] = None
        price_amount: Optional[float] = None
        currency: Optional[str] = None
        if isinstance(price_node, dict):
            price_str = price_node.get("formatted_amount") or price_node.get("text")
            amount = price_node.get("amount")
            if amount is not None:
                try:
                    price_amount = float(amount)
                except (TypeError, ValueError):
                    price_amount = None
            currency = price_node.get("currency")
        elif isinstance(price_node, str):
            price_str = price_node

        # Location
        location: Optional[str] = None
        loc_node = node.get("location") or {}
        if isinstance(loc_node, dict):
            reverse = loc_node.get("reverse_geocode") or {}
            if isinstance(reverse, dict):
                city = reverse.get("city")
                state = reverse.get("state")
                location = ", ".join(
                    p for p in (city, state) if isinstance(p, str) and p
                ) or None

        # Primary image
        image_url: Optional[str] = None
        img = node.get("primary_listing_photo") or node.get("listing_photo") or {}
        if isinstance(img, dict):
            uri = (img.get("image") or {}).get("uri")
            if isinstance(uri, str):
                image_url = uri

        # Seller name
        seller_name: Optional[str] = None
        seller = node.get("marketplace_listing_seller") or node.get("seller") or {}
        if isinstance(seller, dict):
            seller_name = seller.get("name")

        # Creation time
        creation_time: Optional[datetime] = None
        ts = node.get("creation_time") or node.get("created_time")
        if isinstance(ts, (int, float)):
            try:
                creation_time = datetime.fromtimestamp(int(ts), tz=timezone.utc)
            except (OSError, OverflowError, ValueError):
                creation_time = None

        # Vehicle-specific fields
        mileage: Optional[str] = None
        is_new: Optional[bool] = None
        attrs = node.get("vehicle") or {}
        if isinstance(attrs, dict):
            mileage_node = attrs.get("odometer_data") or {}
            if isinstance(mileage_node, dict):
                mileage = mileage_node.get("formatted_mileage")
            condition = attrs.get("condition")
            if isinstance(condition, str):
                is_new = condition.upper() == "NEW"
        if is_new is None:
            cond = node.get("vehicle_condition")
            if isinstance(cond, str):
                is_new = cond.upper() == "NEW"

        is_sold = node.get("is_sold")
        if not isinstance(is_sold, bool):
            is_sold = None
        is_pending = node.get("is_pending")
        if not isinstance(is_pending, bool):
            is_pending = None

        url = f"https://www.facebook.com/marketplace/item/{listing_id}/"

        return MarketplaceVehicleListing(
            id=listing_id,
            url=url,
            title=title,
            price=price_str,
            price_amount=price_amount,
            currency=currency,
            location=location,
            image_url=image_url,
            seller_name=seller_name,
            creation_time=creation_time,
            mileage=mileage,
            is_new=is_new,
            is_sold=is_sold,
            is_pending=is_pending,
            raw=node if _RAW_DEBUG else None,
        )

    # ----- JSON discovery ----------------------------------------------

    def _iter_json_objects(self, html_content: str) -> Iterable[Any]:
        soup = BeautifulSoup(html_content, "html.parser")
        for script in soup.find_all("script"):
            text = script.string or script.get_text() or ""
            if not text or "{" not in text:
                continue
            for obj in _extract_json_objects(text):
                yield obj


_RAW_DEBUG = False


def _walk(obj: Any) -> Iterable[Any]:
    """Yield ``obj`` and every nested dict / list element recursively."""
    stack = [obj]
    while stack:
        cur = stack.pop()
        yield cur
        if isinstance(cur, dict):
            stack.extend(cur.values())
        elif isinstance(cur, list):
            stack.extend(cur)


_OBJ_START_RE = re.compile(r"\{")


def _extract_json_objects(text: str) -> Iterable[Any]:
    """Yield every top-level JSON object that can be decoded inside ``text``.

    Facebook scripts often look like::

        require("ScheduledServerJS").handle({...big json...});
        require("RelayPrefetchedStreamCache").next({...});

    We scan for ``{`` characters and try to incrementally JSON-decode from
    each, advancing past successfully-decoded objects.
    """
    decoder = json.JSONDecoder()
    i = 0
    n = len(text)
    while i < n:
        match = _OBJ_START_RE.search(text, i)
        if not match:
            return
        start = match.start()
        try:
            obj, end = decoder.raw_decode(text, start)
        except ValueError:
            i = start + 1
            continue
        yield obj
        i = end
