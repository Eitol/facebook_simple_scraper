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
            MarketplaceVehicleFilters(location="santiago")
        )
        parsed = urlparse(url)
        self.assertEqual(parsed.netloc, "www.facebook.com")
        self.assertEqual(parsed.path, "/marketplace/santiago/vehicles/")
        self.assertEqual(parse_qs(parsed.query).get("exact"), ["false"])

    def test_query_and_condition(self):
        qs = _qs(MarketplaceVehicleFilters(
            location="santiago",
            condition=VehicleCondition.NEW,
            query="toyota corolla",
        ))
        self.assertEqual(qs["query"], ["toyota corolla"])
        self.assertEqual(qs["itemCondition"], ["NEW"])

    def test_used_condition_groups_subconditions(self):
        qs = _qs(MarketplaceVehicleFilters(
            location="santiago", condition=VehicleCondition.USED,
        ))
        self.assertIn("USED_LIKE_NEW", qs["itemCondition"][0])

    def test_availability_in_stock(self):
        qs = _qs(MarketplaceVehicleFilters(
            location="santiago", availability=VehicleAvailability.IN_STOCK,
        ))
        self.assertEqual(qs["availability"], ["in stock"])

    def test_availability_out_of_stock(self):
        qs = _qs(MarketplaceVehicleFilters(
            location="santiago", availability=VehicleAvailability.OUT_OF_STOCK,
        ))
        self.assertEqual(qs["availability"], ["out of stock"])

    def test_availability_all_omits_param(self):
        qs = _qs(MarketplaceVehicleFilters(
            location="santiago", availability=VehicleAvailability.ALL,
        ))
        self.assertNotIn("availability", qs)

    def test_days_since_listed(self):
        for days in (DaysSinceListed.LAST_DAY,
                     DaysSinceListed.LAST_WEEK,
                     DaysSinceListed.LAST_MONTH):
            qs = _qs(MarketplaceVehicleFilters(
                location="santiago", days_since_listed=days,
            ))
            self.assertEqual(qs["daysSinceListed"], [str(int(days))])

    def test_days_since_listed_any_omits_param(self):
        qs = _qs(MarketplaceVehicleFilters(
            location="santiago", days_since_listed=DaysSinceListed.ANY,
        ))
        self.assertNotIn("daysSinceListed", qs)

    def test_price_range(self):
        qs = _qs(MarketplaceVehicleFilters(
            location="santiago", min_price=1000, max_price=20000,
        ))
        self.assertEqual(qs["minPrice"], ["1000"])
        self.assertEqual(qs["maxPrice"], ["20000"])

    def test_empty_location_raises(self):
        with self.assertRaises(ValueError):
            MarketplaceVehicleRepository._build_url(
                MarketplaceVehicleFilters(location=" / ")
            )


if __name__ == "__main__":
    unittest.main()
