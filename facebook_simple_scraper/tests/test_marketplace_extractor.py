import json
import unittest

from facebook_simple_scraper.marketplace.extractor import MarketplaceListingsExtractor


def _make_html(payload: dict) -> str:
    """Wrap a JSON payload inside the kind of script tag Facebook serves."""
    return (
        "<html><body><script>"
        f'require("ScheduledServerJS").handle({json.dumps(payload)});'
        "</script></body></html>"
    )


class TestMarketplaceListingsExtractor(unittest.TestCase):
    def test_extracts_minimal_listing(self):
        payload = {
            "data": {
                "marketplace_search": {
                    "feed_units": {
                        "edges": [
                            {
                                "node": {
                                    "__typename": "MarketplaceListing",
                                    "id": "123456789",
                                    "marketplace_listing_title": "Toyota Corolla 2020",
                                    "listing_price": {
                                        "formatted_amount": "$10,500",
                                        "amount": 10500,
                                        "currency": "USD",
                                    },
                                    "location": {
                                        "reverse_geocode": {
                                            "city": "Santiago",
                                            "state": "RM",
                                        }
                                    },
                                    "primary_listing_photo": {
                                        "image": {"uri": "https://cdn.fb/img.jpg"}
                                    },
                                    "marketplace_listing_seller": {
                                        "name": "Juan Perez"
                                    },
                                    "creation_time": 1700000000,
                                }
                            }
                        ],
                        "page_info": {"end_cursor": "ABC123"},
                    }
                }
            }
        }

        html = _make_html(payload)
        result = MarketplaceListingsExtractor().extract(html)

        self.assertEqual(len(result.listings), 1)
        listing = result.listings[0]
        self.assertEqual(listing.id, "123456789")
        self.assertEqual(listing.title, "Toyota Corolla 2020")
        self.assertEqual(listing.price, "$10,500")
        self.assertEqual(listing.price_amount, 10500.0)
        self.assertEqual(listing.currency, "USD")
        self.assertEqual(listing.location, "Santiago, RM")
        self.assertEqual(listing.image_url, "https://cdn.fb/img.jpg")
        self.assertEqual(listing.seller_name, "Juan Perez")
        self.assertIn("/marketplace/item/123456789", listing.url)
        self.assertEqual(result.cursor, "ABC123")

    def test_deduplicates_listings(self):
        node = {
            "__typename": "MarketplaceListing",
            "id": "1",
            "marketplace_listing_title": "Car",
        }
        payload = {"a": [node, node]}
        result = MarketplaceListingsExtractor().extract(_make_html(payload))
        self.assertEqual(len(result.listings), 1)

    def test_returns_empty_when_no_listings(self):
        result = MarketplaceListingsExtractor().extract("<html></html>")
        self.assertEqual(result.listings, [])
        self.assertIsNone(result.cursor)


if __name__ == "__main__":
    unittest.main()
