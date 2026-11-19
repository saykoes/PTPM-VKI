"""
End-to-end tests for the Etagi FastAPI endpoint.
Tests the live API endpoint with actual HTTP requests.
"""
import json
import unittest
import urllib.request
import urllib.error


class TestEtagiAPIE2E(unittest.TestCase):
    """E2E tests for the FastAPI search endpoint."""

    API_URL = "http://127.0.0.1:8000/api/realty/search"

    def test_search_endpoint_returns_valid_structure(self):
        """Test search endpoint returns valid JSON structure with expected fields."""
        url = f"{self.API_URL}?rooms=1"
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                self.assertEqual(response.status, 200)
                data = json.loads(response.read().decode("utf-8"))

                self.assertIn("search_url", data)
                self.assertIn("count", data)
                self.assertIn("items", data)
                self.assertIsInstance(data["search_url"], str)
                self.assertIsInstance(data["count"], int)
                self.assertIsInstance(data["items"], list)
                self.assertIn("etagi.com", data["search_url"])
                self.assertIn("realty", data["search_url"])

        except urllib.error.URLError as e:
            self.fail(f"API endpoint not reachable: {e}")

    def test_search_endpoint_with_district_filter_and_square_min(self):
        """Test search endpoint with district_id and square_min filters.
        
        Validates that square_min=80 filter returns only items with area_m2 >= 80.
        """
        url = f"{self.API_URL}?district_ids=38039&square_min=80"
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                self.assertEqual(response.status, 200)
                data = json.loads(response.read().decode("utf-8"))

                self.assertIn("search_url", data)
                self.assertIn("count", data)
                self.assertIn("items", data)
                self.assertIn("district_id", data["search_url"])
                self.assertIn("square_min", data["search_url"])
                
                # Validate square_min filter works correctly
                # All returned items should have area_m2 >= 80
                items = data.get("items", [])
                for item in items:
                    area_m2 = item.get("area_m2")
                    if area_m2 is not None:
                        self.assertGreaterEqual(
                            area_m2, 80,
                            f"Item {item.get('id')} has area_m2={area_m2}, expected >= 80"
                        )

        except urllib.error.URLError as e:
            self.fail(f"API endpoint not reachable: {e}")

    def test_search_endpoint_items_have_required_fields(self):
        """Test that each item in results has required fields."""
        url = f"{self.API_URL}?rooms=2&price_min=5000000"
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))

                items = data.get("items", [])
                if len(items) > 0:
                    item = items[0]
                    self.assertIn("id", item)
                    self.assertIn("url", item)
                    self.assertIn("title", item)
                    self.assertIn("area_m2", item)
                    self.assertIn("floor", item)
                    self.assertIn("price_rub", item)
                    self.assertIn("price_per_m2_rub", item)
                    self.assertIn("address", item)
                    self.assertIn("images", item)
                    self.assertIn("etagi.com", item["url"])

        except urllib.error.URLError as e:
            self.fail(f"API endpoint not reachable: {e}")

    def test_search_endpoint_contains_expected_strings(self):
        """Test that response contains expected strings in URLs and fields."""
        url = f"{self.API_URL}?district_ids=38039"
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))

                self.assertIn("novosibirsk.etagi.com", data["search_url"])
                self.assertIn("realty", data["search_url"])

                items = data.get("items", [])
                if len(items) > 0:
                    first_item = items[0]
                    self.assertIn(first_item.get("id", ""), first_item.get("url", ""))
                    title = first_item.get("title", "").lower()
                    self.assertTrue(any(room_type in title for room_type in ["комн.", "студия"]))
                    address = first_item.get("address", "")
                    self.assertIn("Новосибирск", address)

        except urllib.error.URLError as e:
            self.fail(f"API endpoint not reachable: {e}")

    def test_search_endpoint_with_multiple_rooms(self):
        """Test search endpoint with multiple room filters."""
        url = f"{self.API_URL}?rooms=1&rooms=2&price_min=3000000&price_max=10000000"
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))

                self.assertEqual(response.status, 200)
                self.assertIn("search_url", data)
                self.assertIn("rooms[]=1", data["search_url"])
                self.assertIn("rooms[]=2", data["search_url"])

        except urllib.error.URLError as e:
            self.fail(f"API endpoint not reachable: {e}")


if __name__ == "__main__":
    unittest.main()
