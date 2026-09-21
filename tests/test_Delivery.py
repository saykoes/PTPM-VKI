import unittest
from Delivery import calculate_delivery_cost


class TestDeliveryCost(unittest.TestCase):

    def test_standard_delivery_success(self):
        # 1 Standard values (without additional costs)
        cost, date = calculate_delivery_cost(weight=2.0, distance=100, package_type="обычный")
        self.assertEqual(cost, 700)
        self.assertIn("2026", date)
        self.assertEqual(date, "2026-09-04")

    def test_min_boundaries_success(self):
        # 2 Min values
        cost, date = calculate_delivery_cost(weight=0.1, distance=1, package_type="обычный")
        self.assertTrue(200 < cost <= 210)
        self.assertEqual(date, "2026-09-04")

    def test_max_boundaries_success(self):
        # 3 Max values
        cost, date = calculate_delivery_cost(weight=50.0, distance=5000, package_type="обычный")
        self.assertEqual(cost, 37800)
        self.assertEqual(date, "2026-09-13")

    def test_weight_out_of_bounds_high(self):
        # 4 Too heavy
        cost, date = calculate_delivery_cost(weight=50.1, distance=100, package_type="обычный")
        self.assertEqual(cost, -1)
        self.assertEqual(date, "0000-00-00")

    def test_distance_out_of_bounds_low(self):
        # 5 Distance is too short
        cost, date = calculate_delivery_cost(weight=5.0, distance=0, package_type="обычный")
        self.assertEqual(cost, -1)
        self.assertEqual(date, "0000-00-00")

    def test_invalid_package_type(self):
        # 6 Invalid package type
        cost, date = calculate_delivery_cost(weight=5.0, distance=100, package_type="хрупкое_стекло")
        self.assertEqual(cost, -1)
        self.assertEqual(date, "0000-00-00")

    def tes_medium_weight_and_fragile(self):
        # 7 Additional costs: Medium weight (+20%) and fragile type (+300rub)
        cost, date = calculate_delivery_cost(weight=10.0, distance=500, package_type="хрупкий")
        self.assertEqual(cost, 3540)
        self.assertEqual(date, "2026-09-04")

    def test_heavy_weight_and_hazardous(self):
        # 8 Additional costs: Heavy weight (+50%) and dangerous type (+1000rub)
        cost, date = calculate_delivery_cost(weight=20.0, distance=1000, package_type="опасный")
        self.assertEqual(cost, 8800)
        self.assertEqual(date, "2026-09-05")
        
    def test_express_delivery_modifier(self):
        # 9 Additional costs: Express *1.5 (5200 * 1.5 = 7800)
        cost, date = calculate_delivery_cost(weight=2.0, distance=1000, package_type="обычный", is_express=True)
        self.assertEqual(cost, 7800) 

    def test_express_delivery_zero_days(self):
        # 10 Express delivery: at least 1 day is needed for a delivery
        cost, date = calculate_delivery_cost(weight=2.0, distance=499, package_type="обычный", is_express=True)
        self.assertGreater(date, "2026-09-03")
        self.assertEqual(date, "2026-09-04")

    def test_invalid_weight_type_raise(self):
        # 11. Invalid string
        with self.assertRaises(TypeError):
            calculate_delivery_cost(weight="два килограмма", distance=100, package_type="обычный")

    def test_invalid_distance_type_raise(self):
        # 12. Invalid string
        with self.assertRaises(TypeError):
            calculate_delivery_cost(weight=5.0, distance="сто километров", package_type="обычный")
    
    def test_standard_delivery_types(self):
        # 13. Check for types
        result = calculate_delivery_cost(weight=2.0, distance=100, package_type="обычный")
        
        # 2 element tuple
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        
        # Check types in the tuple
        cost, date_str = result
        self.assertIsInstance(cost, int)
        self.assertIsInstance(date_str, str)

if __name__ == "__main__":
    unittest.main()
