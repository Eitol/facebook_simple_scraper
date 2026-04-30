import unittest
from urllib.parse import parse_qs, urlparse

from facebook_simple_scraper.marketplace.entities import (
    DaysSinceListed,
    MarketplaceVehicleFilters,
    VehicleAvailability,
    VehicleCondition,
)
from facebook_simple_scraper.marketplace.repository import MarketplaceVehicleRepository


def _qs(filters: MarketplaceVehicleFilters) -> dict:
    url = MarketplaceVehicleRepository._build_url(filters)
    return {k: v for k, v in parse_qs(urlparse(url).query).items()}


class TestMarketplaceURLBuilder(unittest.TestCase):
    def test_minimal_url(self):
        url = MarketplaceVehicleRepository._build_url(
            MarketplaceVehicleFilters()
        )
        parsed = urlparse(url)
        self.assertEqual(parsed.netloc, "www.facebook.com")
        self.assertEqual(parsed.path, "/marketplace/category/search/")
        qs = parse_qs(parsed.query)
        self.assertEqual(qs["category_id"], ["807311116002614"])
        self.assertEqual(qs.get("exact"), ["false"])

    def test_slug_url(self):
        # Slug-based URL routes through /{city}/vehicles/ rather than
        # /{city}/search/: the latter responds with an empty feed for
        # most Chilean cities even when the former returns listings.
        url = MarketplaceVehicleRepository._build_url(
            MarketplaceVehicleFilters(location="miami")
        )
        self.assertIn("/marketplace/miami/vehicles/", url)

    def test_slug_url_omits_lat_lng_and_category_id(self):
        # FB derives location from the vanity URL; lat/lng don't take
        # effect via plain HTTP, and the category is implicit in the
        # /vehicles/ slug, so we drop both.
        url = MarketplaceVehicleRepository._build_url(
            MarketplaceVehicleFilters(
                location="ancud",
                latitude=-41.8682, longitude=-73.8287, radius_km=40,
            )
        )
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        self.assertNotIn("latitude", qs)
        self.assertNotIn("longitude", qs)
        self.assertNotIn("radius", qs)
        self.assertNotIn("category_id", qs)

    def test_lat_lng(self):
        qs = _qs(MarketplaceVehicleFilters(
            latitude=-33.4489, longitude=-70.6693, radius_km=50,
        ))
        self.assertEqual(qs["latitude"], ["-33.4489"])
        self.assertEqual(qs["longitude"], ["-70.6693"])
        self.assertEqual(qs["radius"], ["50"])

    def test_query_and_condition(self):
        qs = _qs(MarketplaceVehicleFilters(
            condition=VehicleCondition.NEW,
            query="toyota corolla",
        ))
        self.assertEqual(qs["query"], ["toyota corolla"])
        self.assertEqual(qs["itemCondition"], ["NEW"])

    def test_used_condition_groups_subconditions(self):
        qs = _qs(MarketplaceVehicleFilters(condition=VehicleCondition.USED))
        self.assertIn("USED_LIKE_NEW", qs["itemCondition"][0])

    def test_availability_in_stock(self):
        qs = _qs(MarketplaceVehicleFilters(availability=VehicleAvailability.IN_STOCK))
        self.assertEqual(qs["availability"], ["in stock"])

    def test_availability_out_of_stock(self):
        qs = _qs(MarketplaceVehicleFilters(availability=VehicleAvailability.OUT_OF_STOCK))
        self.assertEqual(qs["availability"], ["out of stock"])

    def test_availability_all_omits_param(self):
        qs = _qs(MarketplaceVehicleFilters(availability=VehicleAvailability.ALL))
        self.assertNotIn("availability", qs)

    def test_days_since_listed(self):
        for days in (DaysSinceListed.LAST_DAY,
                     DaysSinceListed.LAST_WEEK,
                     DaysSinceListed.LAST_MONTH):
            qs = _qs(MarketplaceVehicleFilters(days_since_listed=days))
            self.assertEqual(qs["daysSinceListed"], [str(int(days))])

    def test_days_since_listed_any_omits_param(self):
        qs = _qs(MarketplaceVehicleFilters(days_since_listed=DaysSinceListed.ANY))
        self.assertNotIn("daysSinceListed", qs)

    def test_price_range(self):
        qs = _qs(MarketplaceVehicleFilters(min_price=1000, max_price=20000))
        self.assertEqual(qs["minPrice"], ["1000"])
        self.assertEqual(qs["maxPrice"], ["20000"])


if __name__ == "__main__":
    unittest.main()
