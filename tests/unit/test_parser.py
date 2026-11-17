"""
Unit tests for src/parser.py
Tests parse_raw_card, build_search_url, and extract_cards_from_dom methods.
"""
import unittest
from unittest.mock import MagicMock
from src.parser import EtagiParser


class TestEtagiParserUnit(unittest.TestCase):
    """Unit tests for EtagiParser without Selenium driver."""

    def setUp(self):
        """Create parser instance without launching Edge."""
        self.parser = EtagiParser.__new__(EtagiParser)
        self.parser.timeout = 10
        self.parser.driver = MagicMock()
        self.parser.logger = MagicMock()

    # --- build_search_url Tests ---

    def test_build_search_url_default(self):
        """Test URL construction with no filters."""
        url = self.parser.build_search_url()
        # Base URL should be present
        self.assertIn("etagi.com", url)
        # No query params should be added for default
        self.assertEqual(url.count("?"), 1)

    def test_build_search_url_with_rooms(self):
        """Test URL construction with room filters."""
        url = self.parser.build_search_url(rooms=[1, 2, 3])
        self.assertIn("rooms[]=1", url)
        self.assertIn("rooms[]=2", url)
        self.assertIn("rooms[]=3", url)

    def test_build_search_url_rooms_greater_than_4(self):
        """Test that 4+ rooms is encoded as >4."""
        url = self.parser.build_search_url(rooms=[4, 5])
        self.assertIn("rooms[]=%3E4", url)

    def test_build_search_url_with_price_filters(self):
        """Test URL construction with price filters."""
        url = self.parser.build_search_url(
            price_min=7_000_000,
            price_max=47_000_000
        )
        self.assertIn("price_min=7000000", url)
        self.assertIn("price_max=47000000", url)

    def test_build_search_url_with_square_filters(self):
        """Test URL construction with square meter filters."""
        url = self.parser.build_search_url(
            square_min=80,
            square_max=200
        )
        self.assertIn("square_min=80", url)
        self.assertIn("square_max=200", url)

    def test_build_search_url_with_district_ids(self):
        """Test URL construction with district IDs."""
        url = self.parser.build_search_url(district_ids=[38039, 38040])
        self.assertIn("district_id[]=38039", url)
        self.assertIn("district_id[]=38040", url)

    def test_build_search_url_with_page(self):
        """Test URL construction with page parameter."""
        url = self.parser.build_search_url(page=1)
        self.assertNotIn("page=", url)

        url = self.parser.build_search_url(page=2)
        self.assertIn("page=2", url)

    def test_build_search_url_order_param(self):
        """Test URL construction with order parameter."""
        url = self.parser.build_search_url(order="price_asc")
        self.assertIn("order=price_asc", url)

    # --- parse_raw_card Tests ---

    def test_parse_raw_card_full_card(self):
        """Test parsing a complete card with all fields."""
        raw_card = {
            "links": ["https://novosibirsk.etagi.com/realty/12345678/"],
            "text": (
                "1/70\n"
                "Современный ремонт\n"
                "27 000 000 ₽\n"
                "217 742 ₽/м²\n"
                "3-комн. кв. · 124 м² · 7/15 эт.\n"
                "ул. Красный проспект, 100"
            ),
            "images": [
                "https://example.com/image1.jpg",
                "https://example.com/image2.jpg",
                "https://example.com/image3.jpg"
            ]
        }

        result = self.parser.parse_raw_card(raw_card)

        self.assertIsNotNone(result)
        self.assertEqual(result["id"], "12345678")
        self.assertEqual(result["url"], "https://novosibirsk.etagi.com/realty/12345678/")
        self.assertEqual(result["price_rub"], 27_000_000)
        self.assertEqual(result["price_per_m2_rub"], 217_742)
        self.assertEqual(result["area_m2"], 124.0)
        self.assertIn("3-комн. кв.", result["title"])
        self.assertIn("ул.", result["address"])
        self.assertEqual(len(result["images"]), 3)  # Limited to 3

    def test_parse_raw_card_studio_apartment(self):
        """Test parsing a studio apartment card."""
        raw_card = {
            "links": ["https://novosibirsk.etagi.com/realty/5551234/"],
            "text": (
                "4 200 000 ₽\n"
                "150 000 ₽/м²\n"
                "Студия · 28 м² · 3/12 эт."
            ),
            "images": []
        }

        result = self.parser.parse_raw_card(raw_card)

        self.assertIsNotNone(result)
        self.assertEqual(result["id"], "5551234")
        self.assertEqual(result["price_rub"], 4_200_000)
        self.assertIn("Студия", result["title"])
        self.assertEqual(result["area_m2"], 28.0)

    def test_parse_raw_card_missing_address(self):
        """Test parsing a card without address field."""
        raw_card = {
            "links": ["https://novosibirsk.etagi.com/realty/999/"],
            "text": (
                "5 000 000 ₽\n"
                "100 000 ₽/м²\n"
                "2-комн. кв. · 50 м² · 2/5 эт."
            ),
            "images": []
        }

        result = self.parser.parse_raw_card(raw_card)

        self.assertIsNotNone(result)
        self.assertIsNone(result["address"])

    def test_parse_raw_card_missing_price(self):
        """Test parsing a card without price field."""
        raw_card = {
            "links": ["https://novosibirsk.etagi.com/realty/111/"],
            "text": (
                "150 000 ₽/м²\n"
                "1-комн. кв. · 35 м² · 1/3 эт.\n"
                "ул. Ленина, 1"
            ),
            "images": []
        }

        result = self.parser.parse_raw_card(raw_card)

        self.assertIsNotNone(result)
        self.assertIsNone(result["price_rub"])

    def test_parse_raw_card_invalid_links(self):
        """Test parsing a card with invalid links."""
        raw_card = {
            "links": ["https://example.com/not-realty/123/"],
            "text": "1 000 000 ₽",
            "images": []
        }

        result = self.parser.parse_raw_card(raw_card)

        self.assertIsNone(result)

    def test_parse_raw_card_no_id_in_url(self):
        """Test parsing a card where ID cannot be extracted."""
        raw_card = {
            "links": ["https://novosibirsk.etagi.com/realty/"],
            "text": "1 000 000 ₽",
            "images": []
        }

        result = self.parser.parse_raw_card(raw_card)

        self.assertIsNone(result)

    def test_parse_raw_card_empty_text(self):
        """Test parsing a card with empty text."""
        raw_card = {
            "links": ["https://novosibirsk.etagi.com/realty/123/"],
            "text": "",
            "images": []
        }

        result = self.parser.parse_raw_card(raw_card)

        self.assertIsNotNone(result)
        self.assertEqual(result["id"], "123")
        self.assertIsNone(result["price_rub"])

    def test_parse_raw_card_old_price(self):
        """Test parsing a card with old price (second price)."""
        raw_card = {
            "links": ["https://novosibirsk.etagi.com/realty/222/"],
            "text": (
                "5 000 000 ₽\n"
                "4 500 000 ₽\n"
                "100 000 ₽/м²\n"
                "2-комн. кв. · 50 м²"
            ),
            "images": []
        }

        result = self.parser.parse_raw_card(raw_card)

        self.assertIsNotNone(result)
        self.assertEqual(result["price_rub"], 5_000_000)
        self.assertEqual(result["old_price_rub"], 4_500_000)

    def test_parse_raw_card_image_limit(self):
        """Test that only first 3 images are returned."""
        raw_card = {
            "links": ["https://novosibirsk.etagi.com/realty/333/"],
            "text": "1 000 000 ₽",
            "images": [f"https://img{i}.jpg" for i in range(10)]
        }

        result = self.parser.parse_raw_card(raw_card)

        self.assertEqual(len(result["images"]), 3)

    # --- extract_cards_from_dom Tests ---

    def test_extract_cards_from_dom_returns_list(self):
        """Test that extract_cards_from_dom returns a list."""
        # Card data that can be parsed by parse_raw_card
        self.parser.driver.execute_async_script = MagicMock(
            return_value=[{
                "links": ["https://novosibirsk.etagi.com/realty/111/"],
                "text": "1 000 000 ₽",
                "images": []
            }]
        )

        result = self.parser.extract_cards_from_dom("selector")

        self.assertIsInstance(result, list)

    def test_extract_cards_from_dom_calls_js(self):
        """Test that extract_cards_from_dom calls the JS script."""
        self.parser.driver.execute_async_script = MagicMock(return_value=[])

        self.parser.extract_cards_from_dom("test_selector")

        self.parser.driver.execute_async_script.assert_called_once()

    def test_extract_cards_from_dom_empty_result(self):
        """Test extract_cards_from_dom with empty result."""
        self.parser.driver.execute_async_script = MagicMock(return_value=[])

        result = self.parser.extract_cards_from_dom("selector")

        self.assertEqual(result, [])

    def test_extract_cards_from_dom_multiple_cards(self):
        """Test extract_cards_from_dom with multiple cards."""
        self.parser.driver.execute_async_script = MagicMock(
            return_value=[
                {
                    "links": ["https://novosibirsk.etagi.com/realty/111/"],
                    "text": "1 000 000 ₽",
                    "images": []
                },
                {
                    "links": ["https://novosibirsk.etagi.com/realty/222/"],
                    "text": "2 000 000 ₽",
                    "images": []
                },
            ]
        )

        result = self.parser.extract_cards_from_dom("selector")

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], "111")
        self.assertEqual(result[1]["id"], "222")


if __name__ == "__main__":
    unittest.main()
