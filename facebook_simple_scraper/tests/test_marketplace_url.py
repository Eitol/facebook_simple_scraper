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
        url = MarketplaceVehicleRepository._build_url(
            MarketplaceVehicleFilters(location="miami")
        )
        self.assertIn("/marketplace/miami/search/", url)

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
