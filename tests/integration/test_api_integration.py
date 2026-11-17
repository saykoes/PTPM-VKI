"""
Integration tests for the Etagi FastAPI endpoint.
Tests the FastAPI app integration with the EtagiParser.
"""
import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from src.api import app, parser_instance, driver_lock


class TestEtagiAPI(unittest.TestCase):
    """Test the FastAPI search endpoint."""

    def setUp(self):
        self.client = TestClient(app)

    def test_search_endpoint_returns_200_with_valid_params(self):
        """Test search endpoint returns 200 and valid response structure."""
        with patch("src.api.parser_instance") as mock_parser:
            mock_parser.search.return_value = {
                "search_url": "https://novosibirsk.etagi.com/realty/?rooms[]=2",
                "count": 2,
                "items": [
                    {
                        "id": "123",
                        "url": "https://novosibirsk.etagi.com/realty/123/",
                        "title": "2-комн. кв.",
                        "area_m2": 65.0,
                        "floor": "3/10 эт.",
                        "price_rub": 12_000_000,
                        "old_price_rub": None,
                        "price_per_m2_rub": 184_615,
                        "address": "ул. Ленина, 10",
                        "images": ["https://img1.jpg"],
                        "raw_lines": []
                    },
                    {
                        "id": "456",
                        "url": "https://novosibirsk.etagi.com/realty/456/",
                        "title": "1-комн. кв.",
                        "area_m2": 35.0,
                        "floor": "1/5 эт.",
                        "price_rub": 7_000_000,
                        "old_price_rub": None,
                        "price_per_m2_rub": 200_000,
                        "address": "ул. Красная, 5",
                        "images": ["https://img2.jpg"],
                        "raw_lines": []
                    }
                ]
            }
            response = self.client.get(
                "/api/realty/search",
                params={"rooms": [2], "price_min": 5_000_000, "price_max": 15_000_000}
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("search_url", data)
            self.assertIn("count", data)
            self.assertIn("items", data)
            self.assertEqual(data["count"], 2)
            self.assertEqual(len(data["items"]), 2)
            self.assertEqual(data["items"][0]["id"], "123")

    def test_search_endpoint_handles_scraper_exception(self):
        """Test search endpoint returns 500 when scraper fails."""
        with patch("src.api.parser_instance") as mock_parser:
            mock_parser.search.side_effect = RuntimeError("Scraping failed")
            response = self.client.get(
                "/api/realty/search",
                params={"rooms": [1]}
            )
            self.assertEqual(response.status_code, 500)
            data = response.json()
            self.assertIn("detail", data)
            self.assertIn("Scraping failed", data["detail"])

    def test_search_endpoint_rejects_invalid_params(self):
        """Test search endpoint validates query parameters."""
        # Negative price
        response = self.client.get(
            "/api/realty/search",
            params={"price_min": -100}
        )
        self.assertEqual(response.status_code, 422)

        # Negative page
        response = self.client.get(
            "/api/realty/search",
            params={"page": 0}
        )
        self.assertEqual(response.status_code, 422)

        # Invalid square (must be > 0)
        response = self.client.get(
            "/api/realty/search",
            params={"square_min": 0}
        )
        self.assertEqual(response.status_code, 422)

    def test_search_endpoint_passes_all_filters_to_parser(self):
        """Test that all query params are passed to parser.search()."""
        with patch("src.api.parser_instance") as mock_parser:
            mock_parser.search.return_value = {
                "search_url": "",
                "count": 0,
                "items": []
            }
            response = self.client.get(
                "/api/realty/search",
                params={
                    "rooms": [2, 3],
                    "price_min": 5_000_000,
                    "price_max": 30_000_000,
                    "square_min": 50,
                    "square_max": 100,
                    "district_ids": [38039],
                    "street_ids": [123],
                    "newcomplex_ids": [456],
                    "floor_min": 2,
                    "floor_max": 10,
                    "building_year_min": 2000,
                    "order": "date_desc",
                    "page": 2
                }
            )
            self.assertEqual(response.status_code, 200)
            mock_parser.search.assert_called_once()
            call_kwargs = mock_parser.search.call_args.kwargs
            self.assertEqual(call_kwargs["rooms"], [2, 3])
            self.assertEqual(call_kwargs["price_min"], 5_000_000)
            self.assertEqual(call_kwargs["price_max"], 30_000_000)
            self.assertEqual(call_kwargs["square_min"], 50)
            self.assertEqual(call_kwargs["square_max"], 100)
            self.assertEqual(call_kwargs["district_ids"], [38039])
            self.assertEqual(call_kwargs["street_ids"], [123])
            self.assertEqual(call_kwargs["newcomplex_ids"], [456])
            self.assertEqual(call_kwargs["floor_min"], 2)
            self.assertEqual(call_kwargs["floor_max"], 10)
            self.assertEqual(call_kwargs["building_year_min"], 2000)
            self.assertEqual(call_kwargs["order"], "date_desc")
            self.assertEqual(call_kwargs["page"], 2)

    def test_search_endpoint_uses_driver_lock(self):
        """Test that search endpoint uses driver_lock for thread safety."""
        with patch("src.api.driver_lock") as mock_lock:
            mock_lock.__enter__ = MagicMock()
            mock_lock.__exit__ = MagicMock()
            with patch("src.api.parser_instance") as mock_parser:
                mock_parser.search.return_value = {
                    "search_url": "",
                    "count": 0,
                    "items": []
                }
                self.client.get(
                    "/api/realty/search",
                    params={"rooms": [1]}
                )
                mock_lock.__enter__.assert_called_once()
                mock_lock.__exit__.assert_called_once()


if __name__ == "__main__":
    unittest.main()
