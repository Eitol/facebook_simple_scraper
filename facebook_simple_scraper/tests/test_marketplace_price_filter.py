import unittest

from facebook_simple_scraper.marketplace.entities import MarketplaceVehicleFilters
from facebook_simple_scraper.marketplace.repository import _price_in_range


class TestPriceInRange(unittest.TestCase):
    def test_no_bounds_accepts_any_price(self):
        f = MarketplaceVehicleFilters()
        self.assertTrue(_price_in_range(0, f))
        self.assertTrue(_price_in_range(1_000_000, f))
        self.assertTrue(_price_in_range(None, f))

    def test_min_only_excludes_below(self):
        f = MarketplaceVehicleFilters(min_price=30_500_000)
        self.assertFalse(_price_in_range(30_499_999, f))
        self.assertTrue(_price_in_range(30_500_000, f))
        self.assertTrue(_price_in_range(99_000_000, f))

    def test_max_only_excludes_above(self):
        f = MarketplaceVehicleFilters(max_price=10_000_000)
        self.assertTrue(_price_in_range(9_999_999, f))
        self.assertTrue(_price_in_range(10_000_000, f))
        self.assertFalse(_price_in_range(10_000_001, f))

    def test_min_and_max(self):
        f = MarketplaceVehicleFilters(min_price=5_000_000, max_price=10_000_000)
        self.assertFalse(_price_in_range(4_999_999, f))
        self.assertTrue(_price_in_range(5_000_000, f))
        self.assertTrue(_price_in_range(7_500_000, f))
        self.assertTrue(_price_in_range(10_000_000, f))
        self.assertFalse(_price_in_range(10_000_001, f))

    def test_missing_price_is_kept(self):
        """Listings without a parseable price should pass the filter."""
        f = MarketplaceVehicleFilters(min_price=30_500_000, max_price=99_000_000)
        self.assertTrue(_price_in_range(None, f))


if __name__ == "__main__":
    unittest.main()
