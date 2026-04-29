import json
import os
import unittest

from facebook_simple_scraper.marketplace.extractor import (
    MarketplaceDetailExtractor,
    MarketplaceListingsExtractor,
)


_DETAIL_HTML_PATH = "/tmp/detail.html"
_DETAIL2_HTML_PATH = "/tmp/detail2.html"


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
                                        "name": "Juan Perez",
                                        "id": "12345",
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
        self.assertEqual(listing.seller_id, "12345")
        self.assertIn("profile.php?id=12345", listing.seller_url)
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


class TestMarketplaceDetailExtractor(unittest.TestCase):
    def _make_detail_html(self, listing_id: str, **extra) -> str:
        """Build a minimal detail-page HTML for *listing_id*."""
        node = {
            "__typename": "GroupCommerceProductItem",
            "id": listing_id,
            "marketplace_listing_title": "Honda Civic 2019",
            "formatted_price": {"text": "$8,000"},
            "listing_price": {"amount": "8000", "currency": "USD"},
            "location_text": {"text": "Miami, FL"},
            "redacted_description": {"text": "Great condition, low miles"},
            "creation_time": 1700000000,
            "is_sold": False,
            "is_pending": False,
            "listing_photos": [
                {
                    "__typename": "Photo",
                    "image": {"uri": "https://cdn.fb/photo1.jpg"},
                    "id": "p1",
                },
                {
                    "__typename": "Photo",
                    "image": {"uri": "https://cdn.fb/photo2.jpg"},
                    "id": "p2",
                },
            ],
        }
        node.update(extra)
        return _make_html({"listing": node})

    def test_extracts_title_and_price(self):
        html = self._make_detail_html("999")
        detail = MarketplaceDetailExtractor().extract(html, "999")
        self.assertIsNotNone(detail)
        self.assertEqual(detail.id, "999")
        self.assertEqual(detail.title, "Honda Civic 2019")
        self.assertEqual(detail.price, "$8,000")
        self.assertEqual(detail.price_amount, 8000.0)
        self.assertEqual(detail.currency, "USD")

    def test_extracts_images(self):
        html = self._make_detail_html("999")
        detail = MarketplaceDetailExtractor().extract(html, "999")
        self.assertEqual(len(detail.images), 2)
        self.assertIn("photo1.jpg", detail.images[0])
        self.assertIn("photo2.jpg", detail.images[1])

    def test_extracts_description_and_location(self):
        html = self._make_detail_html("999")
        detail = MarketplaceDetailExtractor().extract(html, "999")
        self.assertEqual(detail.description, "Great condition, low miles")
        self.assertEqual(detail.location, "Miami, FL")

    def test_extracts_creation_time(self):
        html = self._make_detail_html("999")
        detail = MarketplaceDetailExtractor().extract(html, "999")
        self.assertIsNotNone(detail.creation_time)
        self.assertEqual(detail.creation_time.year, 2023)

    def test_returns_none_for_unknown_id(self):
        html = self._make_detail_html("999")
        detail = MarketplaceDetailExtractor().extract(html, "000")
        self.assertIsNone(detail)

    def test_merges_multiple_nodes_for_same_id(self):
        """Nodes with the same ID should be merged (photos + description)."""
        node_a = {
            "__typename": "GroupCommerceProductItem",
            "id": "42",
            "marketplace_listing_title": "Car",
            "listing_photos": [
                {"__typename": "Photo", "image": {"uri": "https://cdn.fb/img.jpg"}, "id": "p1"}
            ],
        }
        node_b = {
            "__typename": "GroupCommerceProductItem",
            "id": "42",
            "redacted_description": {"text": "Nice car"},
        }
        html = (
            "<html><body>"
            f"<script>x({json.dumps(node_a)});</script>"
            f"<script>x({json.dumps(node_b)});</script>"
            "</body></html>"
        )
        detail = MarketplaceDetailExtractor().extract(html, "42")
        self.assertIsNotNone(detail)
        self.assertEqual(len(detail.images), 1)
        self.assertEqual(detail.description, "Nice car")

    def test_seller_url_from_logging_id(self):
        """seller_url should be constructed from logging_id when seller.id is absent."""
        node = {
            "__typename": "GroupCommerceProductItem",
            "id": "55",
            "marketplace_listing_title": "Car",
            "logging_id": "99887766",
        }
        html = _make_html({"listing": node})
        detail = MarketplaceDetailExtractor().extract(html, "55")
        self.assertIsNotNone(detail)
        self.assertIsNotNone(detail.seller_url)
        self.assertIn("profile.php?id=99887766", detail.seller_url)

    def test_vehicle_color_fields(self):
        """vehicle_exterior_color and vehicle_interior_color should be extracted."""
        html = self._make_detail_html(
            "77",
            vehicle_exterior_color="grey",
            vehicle_interior_color="black",
        )
        detail = MarketplaceDetailExtractor().extract(html, "77")
        self.assertEqual(detail.vehicle_exterior_color, "grey")
        self.assertEqual(detail.vehicle_interior_color, "black")

    def test_vehicle_interior_color_empty_string_becomes_none(self):
        html = self._make_detail_html("88", vehicle_interior_color="")
        detail = MarketplaceDetailExtractor().extract(html, "88")
        self.assertIsNone(detail.vehicle_interior_color)

    @unittest.skipUnless(os.path.exists(_DETAIL2_HTML_PATH), "detail2.html not available")
    def test_live_detail2_html_color_and_seller(self):
        """Integration test: listing 1737150430583101 should have grey exterior color."""
        with open(_DETAIL2_HTML_PATH) as f:
            html = f.read()
        detail = MarketplaceDetailExtractor().extract(html, "1737150430583101")
        self.assertIsNotNone(detail)
        self.assertEqual(detail.vehicle_exterior_color, "grey")
        self.assertIsNotNone(detail.seller_url)
        self.assertIn("profile.php?id=", detail.seller_url)

    @unittest.skipUnless(os.path.exists(_DETAIL_HTML_PATH), "detail.html not available")
    def test_live_detail_html(self):
        """Integration test against the cached real detail page."""
        with open(_DETAIL_HTML_PATH) as f:
            html = f.read()
        detail = MarketplaceDetailExtractor().extract(html, "1257546456545056")
        self.assertIsNotNone(detail)
        self.assertIsNotNone(detail.title)
        self.assertGreater(len(detail.images), 5)
        self.assertIsNotNone(detail.description)
        self.assertIsNotNone(detail.creation_time)
        self.assertEqual(detail.location, "El Monte, RM")


if __name__ == "__main__":
    unittest.main()
