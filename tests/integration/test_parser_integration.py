"""
Integration tests for EtagiParser.
Tests interactions between multiple parser methods.
"""
import unittest
from unittest.mock import MagicMock, patch
from src.parser import EtagiParser


class TestEtagiParserIntegration(unittest.TestCase):
    """Integration tests for EtagiParser - tests method combinations."""

    def setUp(self):
        """Create parser instance with mocked driver."""
        self.parser = EtagiParser.__new__(EtagiParser)
        self.parser.timeout = 10
        self.parser.driver = MagicMock()
        self.parser.logger = MagicMock()

    def test_search_flow_url_construction_and_parsing(self):
        """Test URL construction with filters."""
        url = self.parser.build_search_url(
            rooms=[2, 3], price_min=5_000_000, price_max=30_000_000,
            district_ids=[38039], page=1
        )
        self.assertIn("rooms[]=2", url)
        self.assertIn("rooms[]=3", url)
        self.assertIn("price_min=5000000", url)
        self.assertIn("price_max=30000000", url)
        self.assertIn("district_id[]=38039", url)
        self.assertNotIn("page=", url)

    def test_parse_raw_card_various_patterns(self):
        """Test parse_raw_card with different URL patterns."""
        test_cases = [
            {
                "links": ["https://novosibirsk.etagi.com/realty/12345678/"],
                "text": "2-комн. кв. · 65 м² · 3/10 эт.\n10 000 000 ₽\n150 000 ₽/м²",
                "expected_id": "12345678", "expected_area": 65.0,
            },
            {
                "links": ["https://novosibirsk.etagi.com/realty/87654321/"],
                "text": "Студия · 30 м² · 1/5 эт.\n5 500 000 ₽",
                "expected_id": "87654321", "expected_area": 30.0,
            },
            {
                "links": ["https://novosibirsk.etagi.com/zastr/55555555/"],
                "text": "3-комн. кв. · 110 м² · 12/24 эт.\n45 000 000 ₽",
                "expected_id": "55555555", "expected_area": 110.0,
            },
        ]
        for case in test_cases:
            with self.subTest(id=case["expected_id"]):
                result = self.parser.parse_raw_card({
                    "links": case["links"], "text": case["text"], "images": []
                })
                self.assertIsNotNone(result)
                self.assertEqual(result["id"], case["expected_id"])
                self.assertEqual(result["area_m2"], case["expected_area"])

    def test_extract_and_parse_single_card(self):
        """Test extraction and parsing of a single card."""
        mock_card = {
            "links": ["https://novosibirsk.etagi.com/realty/111222333/"],
            "text": "2-комн. кв. · 45 м² · 2/9 эт.\n7 500 000 ₽",
            "images": ["https://image1.jpg"]
        }
        self.parser.driver.execute_async_script = MagicMock(return_value=[mock_card])
        result = self.parser.extract_cards_from_dom("selector")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "111222333")
        self.assertEqual(result[0]["area_m2"], 45.0)
        self.assertEqual(result[0]["price_rub"], 7_500_000)

    def test_extract_and_parse_multiple_cards(self):
        """Test extraction and parsing of multiple cards."""
        mock_cards = [
            {"links": ["https://novosibirsk.etagi.com/realty/100/"],
             "text": "2-комн. кв. · 70 м² · 5/12 эт.\n15 000 000 ₽", "images": ["img1.jpg"]},
            {"links": ["https://novosibirsk.etagi.com/realty/200/"],
             "text": "3-комн. кв. · 95 м² · 8/24 эт.\n25 000 000 ₽", "images": ["img2.jpg"]},
            {"links": ["https://novosibirsk.etagi.com/realty/300/"],
             "text": "Студия · 25 м² · 1/5 эт.\n4 000 000 ₽", "images": ["img3.jpg"]},
        ]
        self.parser.driver.execute_async_script = MagicMock(return_value=mock_cards)
        result = self.parser.extract_cards_from_dom("selector")
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["id"], "100")
        self.assertEqual(result[0]["area_m2"], 70.0)
        self.assertEqual(result[0]["price_rub"], 15_000_000)
        self.assertEqual(result[1]["id"], "200")
        self.assertEqual(result[1]["area_m2"], 95.0)
        self.assertEqual(result[1]["price_rub"], 25_000_000)
        self.assertEqual(result[2]["id"], "300")
        self.assertEqual(result[2]["area_m2"], 25.0)
        self.assertEqual(result[2]["price_rub"], 4_000_000)

    def test_extract_cards_handles_empty_result(self):
        """Test empty DOM extraction."""
        self.parser.driver.execute_async_script = MagicMock(return_value=[])
        result = self.parser.extract_cards_from_dom("selector")
        self.assertEqual(result, [])
        self.parser.driver.execute_async_script.assert_called_once()

    @patch("src.parser.EtagiParser.extract_cards_from_dom")
    @patch("selenium.webdriver.support.wait.WebDriverWait")
    def test_search_integration(self, mock_wait_class, mock_extract):
        """Test complete search flow with mocked extraction."""
        # Mock driver.current_url to return a valid URL for urlparse
        self.parser.driver.current_url = "https://novosibirsk.etagi.com/realty/"
        
        # Mock WebDriverWait instance
        mock_wait_instance = MagicMock()
        mock_wait_class.return_value = mock_wait_instance
        mock_wait_instance.until.return_value = None  # Skip waiting
        
        # Mock driver.find_elements and find_element for WebDriverWait condition
        self.parser.driver.find_elements = MagicMock(return_value=[])
        
        mock_element = MagicMock()
        mock_element.text = "0 предложений найдено"
        self.parser.driver.find_element = MagicMock(return_value=mock_element)
        
        mock_extract.return_value = [
            {"id": "123", "url": "https://.../realty/123/", "title": "2-комн. кв.",
             "area_m2": 65.0, "floor": "3/10 эт.", "price_rub": 12_000_000,
             "old_price_rub": None, "price_per_m2_rub": 184_615,
             "address": "ул. Ленина, 10", "images": ["https://img1.jpg"], "raw_lines": []},
            {"id": "456", "url": "https://.../realty/456/", "title": "1-комн. кв.",
             "area_m2": 35.0, "floor": "1/5 эт.", "price_rub": 7_000_000,
             "old_price_rub": None, "price_per_m2_rub": 200_000,
             "address": "ул. Красная, 5", "images": ["https://img2.jpg"], "raw_lines": []},
        ]
        result = self.parser.search(
            rooms=[1, 2], price_min=5_000_000, price_max=15_000_000, district_ids=[38039]
        )
        self.assertIn("search_url", result)
        self.assertIn("count", result)
        self.assertIn("items", result)
        self.assertEqual(result["count"], 2)
        self.assertEqual(len(result["items"]), 2)
        self.assertEqual(result["items"][0]["id"], "123")
        self.assertEqual(result["items"][1]["id"], "456")
        mock_extract.assert_called()


if __name__ == "__main__":
    unittest.main()