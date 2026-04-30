import unittest

from facebook_simple_scraper.marketplace.entities import MarketplaceVehicleFilters
from facebook_simple_scraper.marketplace.extractor import _parse_price_string
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


class TestParsePriceString(unittest.TestCase):
    def test_clp_thousands_dot(self):
        self.assertEqual(_parse_price_string("$20.999.990"), 20999990.0)
        self.assertEqual(_parse_price_string("$110.000"), 110000.0)
        self.assertEqual(_parse_price_string("$15.000"), 15000.0)

    def test_us_decimal_dot(self):
        self.assertEqual(_parse_price_string("$1234.56"), 1234.56)
        self.assertEqual(_parse_price_string("$10.50"), 10.50)

    def test_thousands_comma(self):
        self.assertEqual(_parse_price_string("$10,500"), 10500.0)
        self.assertEqual(_parse_price_string("$1,234,567"), 1234567.0)

    def test_us_decimal_comma(self):
        self.assertEqual(_parse_price_string("$1.234,56"), 1234.56)

    def test_picks_first_number_when_two(self):
        # FB renders "current $5.400.000 was $6.500.000" -> take current
        self.assertEqual(_parse_price_string("$5.400.000 $6.500.000"), 5400000.0)

    def test_with_currency_prefix(self):
        self.assertEqual(_parse_price_string("CLP 30.500.000"), 30500000.0)
        self.assertEqual(_parse_price_string("US$1,234.56"), 1234.56)

    def test_empty_or_none(self):
        self.assertIsNone(_parse_price_string(None))
        self.assertIsNone(_parse_price_string(""))
        self.assertIsNone(_parse_price_string("Free"))


if __name__ == "__main__":
    unittest.main()
