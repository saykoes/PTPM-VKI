import unittest
from unittest.mock import MagicMock

from Triangle import Triangle
from TCalculate import TriangleValidationError, TriangleCalculate

class TestTriangleMockExample(unittest.TestCase):
    """Using MagicMock to substitute a data object"""

    def test_calculate_points_with_mock_triangle(self):
        mock_triangle = MagicMock()

        mock_triangle.side_a = 3.0
        mock_triangle.side_b = 4.0
        mock_triangle.side_c = 5.0

        canvas_size = 100
        points = TriangleCalculate.get_triangle_points(mock_triangle, canvas_size=canvas_size)

        self.assertEqual(len(points), 3)
        for x, y in points:
            self.assertTrue(0 <= x <= canvas_size)
            self.assertTrue(0 <= y <= canvas_size)

class TestTriangleCalculator(unittest.TestCase):
    
    def test_validate_geometry_valid(self):
        """Should pass silently"""
        try:
            TriangleCalculate._validate_geometry(3, 4, 5)
        except TriangleValidationError:
            self.fail("TriangleValidationError raised unexpectedly for valid sides")

    def test_validate_geometry_invalid(self):
        """Should raise TriangleValidationError"""
        with self.assertRaises(TriangleValidationError):
            TriangleCalculate._validate_geometry(1, 2, 10)

    def test_get_triangle_points_scaling(self):
        """Triangle should have 3 points and be in bounds of canvas"""
        triangle = Triangle(3.0, 4.0, 5.0)
        canvas_size = 100
        points = TriangleCalculate.get_triangle_points(triangle, canvas_size=canvas_size)
        
        # Verify 3 vertices are returned
        self.assertEqual(len(points), 3)
        
        # Verify points fit entirely within the 0-100 canvas range
        for x, y in points:
            self.assertTrue(0 <= x <= canvas_size)
            self.assertTrue(0 <= y <= canvas_size)

if __name__ == '__main__':
    unittest.main()
