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
    MarketplaceListingDetail,
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
        return _iter_json_objects_from_html(html_content)


_RAW_DEBUG = False


class MarketplaceDetailExtractor:
    """Extracts full listing detail from a Facebook Marketplace item page.

    The detail page embeds multiple ``GroupCommerceProductItem`` nodes in
    the inline JSON. Each node for the same listing ID can carry different
    fields, so we merge all matching nodes into a single record before
    extracting.
    """

    def extract(
        self, html_content: str, listing_id: str
    ) -> Optional[MarketplaceListingDetail]:
        """Parse *html_content* and return the detail for *listing_id*."""
        nodes: Dict[str, Dict[str, Any]] = {}

        for obj in _iter_json_objects_from_html(html_content):
            for node in _walk(obj):
                if not isinstance(node, dict):
                    continue
                if node.get("__typename") != "GroupCommerceProductItem":
                    continue
                nid = str(node.get("id") or "")
                if nid:
                    if nid not in nodes:
                        nodes[nid] = {}
                    nodes[nid].update(node)

        merged = nodes.get(str(listing_id))
        if merged is None:
            return None
        return self._parse_detail(merged, listing_id)

    @staticmethod
    def _parse_detail(node: Dict[str, Any], listing_id: str) -> MarketplaceListingDetail:
        url = f"https://www.facebook.com/marketplace/item/{listing_id}/"

        title = (
            node.get("marketplace_listing_title")
            or node.get("custom_title")
        )

        price_str: Optional[str] = None
        price_amount: Optional[float] = None
        currency: Optional[str] = None
        fmt_price = node.get("formatted_price")
        if isinstance(fmt_price, dict):
            price_str = fmt_price.get("text")
        price_node = node.get("listing_price") or {}
        if isinstance(price_node, dict):
            if not price_str:
                price_str = price_node.get("formatted_amount")
            amount = price_node.get("amount")
            if amount is not None:
                try:
                    price_amount = float(amount)
                except (TypeError, ValueError):
                    pass
            currency = price_node.get("currency")

        # Location — prefer location_text (human-readable) over lat/lng
        location: Optional[str] = None
        loc_text = node.get("location_text")
        if isinstance(loc_text, dict):
            location = loc_text.get("text") or None
        if location is None:
            loc_node = node.get("location") or {}
            if isinstance(loc_node, dict):
                reverse = loc_node.get("reverse_geocode") or {}
                if isinstance(reverse, dict):
                    city = reverse.get("city")
                    state = reverse.get("state")
                    location = ", ".join(
                        p for p in (city, state) if isinstance(p, str) and p
                    ) or None

        # All photos
        images: List[str] = []
        for photo in node.get("listing_photos") or []:
            if not isinstance(photo, dict):
                continue
            uri = (photo.get("image") or {}).get("uri")
            if isinstance(uri, str):
                images.append(uri)

        # Seller name
        seller_name: Optional[str] = None
        seller = node.get("marketplace_listing_seller") or node.get("seller") or {}
        if isinstance(seller, dict):
            seller_name = seller.get("name")

        # Description — FB uses redacted_description for the visible snippet
        description: Optional[str] = None
        desc_node = node.get("redacted_description") or node.get("description")
        if isinstance(desc_node, dict):
            description = desc_node.get("text")
        elif isinstance(desc_node, str):
            description = desc_node

        # Timestamps
        creation_time: Optional[datetime] = None
        ts = node.get("creation_time") or node.get("created_time")
        if isinstance(ts, (int, float)):
            try:
                creation_time = datetime.fromtimestamp(int(ts), tz=timezone.utc)
            except (OSError, OverflowError, ValueError):
                pass

        # Vehicle-specific
        mileage: Optional[str] = None
        odo = node.get("vehicle_odometer_data") or {}
        if isinstance(odo, dict):
            val = odo.get("value")
            unit = odo.get("unit")
            if val is not None:
                mileage = f"{val} {unit}" if unit else str(val)

        def _str_or_none(v: Any) -> Optional[str]:
            return v if isinstance(v, str) else None

        is_sold = node.get("is_sold")
        if not isinstance(is_sold, bool):
            is_sold = None
        is_pending = node.get("is_pending")
        if not isinstance(is_pending, bool):
            is_pending = None

        return MarketplaceListingDetail(
            id=listing_id,
            url=url,
            title=title,
            price=price_str,
            price_amount=price_amount,
            currency=currency,
            description=description,
            location=location,
            images=images,
            seller_name=seller_name,
            creation_time=creation_time,
            is_sold=is_sold,
            is_pending=is_pending,
            mileage=mileage,
            vehicle_make=_str_or_none(node.get("vehicle_make_display_name")),
            vehicle_model=_str_or_none(node.get("vehicle_model_display_name")),
            vehicle_condition=_str_or_none(node.get("vehicle_condition")),
            vehicle_transmission=_str_or_none(node.get("vehicle_transmission_type")),
            vehicle_fuel_type=_str_or_none(node.get("vehicle_fuel_type")),
            vehicle_exterior_color=_str_or_none(node.get("vehicle_exterior_color")),
            raw=node if _RAW_DEBUG else None,
        )


def _iter_json_objects_from_html(html_content: str) -> Iterable[Any]:
    """Yield JSON objects found inside all ``<script>`` blocks of *html_content*."""
    soup = BeautifulSoup(html_content, "html.parser")
    for script in soup.find_all("script"):
        text = script.string or script.get_text() or ""
        if not text or "{" not in text:
            continue
        for obj in _extract_json_objects(text):
            yield obj


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
