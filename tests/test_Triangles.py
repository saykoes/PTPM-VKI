import math
import unittest

from Triangles import (
    TriangleValidationError,
    convert_float,
    get_triangle_points,
)

class TestTrianglePipeline(unittest.TestCase):
    
    # Тест convert_float

    def test_convert_float_valid_float(self):
        # 1 float
        self.assertEqual(convert_float("12.34"), 12.34)

    def test_convert_float_with_whitespace(self):
        # 2 whitespaces
        self.assertEqual(convert_float("  5.5  "), 5.5)

    def test_convert_float_negative_number(self):
        # 3 negative values
        self.assertEqual(convert_float("-3.14"), -3.14)

    def test_convert_float_invalid_string_raises_value_error(self):
        # 4 invalid string
        with self.assertRaises(ValueError) as context:
            convert_float("abc")
        self.assertIn("Invalid float: 'abc'", str(context.exception))

    def test_convert_float_empty_string_raises_value_error(self):
        # 5 empty string
        with self.assertRaises(ValueError):
            convert_float("")

    # Тест TriangleValidationError
    
    def test_triangle_validation_rule_violation_impossible(self):
        # 6 geo contraints of triangle check (side is too big)
        with self.assertRaises(TriangleValidationError):
            get_triangle_points(1.0, 1.0, 10.0)

    def test_triangle_validation_degenerate_flat(self):
        # 7 (a + b == c) must raise error
        with self.assertRaises(TriangleValidationError):
            get_triangle_points(3.0, 4.0, 7.0)

    def test_triangle_validation_zero_sides(self):
        # 8 0 sides triangle
        with self.assertRaises(TriangleValidationError):
            get_triangle_points(0, 0, 0)

    def test_triangle_validation_negative_sides(self):
        # 9 negative sides triangle
        with self.assertRaises(TriangleValidationError):
            get_triangle_points(-3.0, 4.0, 5.0)

    # Different triangles
    
    def test_equilateral_triangle_execution(self):
        # 10 Equilateral triangle
        points = get_triangle_points(5.0, 5.0, 5.0, canvas_size=100)
        self.assertEqual(len(points), 3)

    def test_right_angled_triangle_coordinates(self):
        # 11 Piphagorous (3, 4, 5) trianlge
        points = get_triangle_points(3.0, 4.0, 5.0, canvas_size=100)
        self.assertEqual(len(points), 3)

    def test_obtuse_triangle_handling(self):
        # 12 Obtuse traingles (goes into negative x-space)
        points = get_triangle_points(5.0, 2.0, 4.0, canvas_size=100)
        self.assertEqual(len(points), 3)

    # Scaling and placing triangle in a pixel grid
     
    def test_canvas_boundaries_fit(self):
        # 13 coords must be in bound of our canvas
        canvas_size = 200
        points = get_triangle_points(10.0, 15.0, 20.0, canvas_size=canvas_size)
        for x, y in points:
            self.assertTrue(0 <= x <= canvas_size)
            self.assertTrue(0 <= y <= canvas_size)

    def test_canvas_size_scaling_large(self):
        # 14 big canvas (1000px)
        points = get_triangle_points(3, 4, 5, canvas_size=1000)
        # Check that it was fitted as much as possible
        max_x = max(p[0] for p in points)
        self.assertEqual(max_x, 1000)

    def test_canvas_size_scaling_small(self):
        # 15 small canvase (10px)
        points = get_triangle_points(300, 400, 500, canvas_size=10)
        for x, y in points:
            self.assertTrue(0 <= x <= 10)
            self.assertTrue(0 <= y <= 10)

    def test_triangle_always_touches_borders_width_or_height(self):
        # 16 shape needs to touch both max points on canvas (0, canvas_size)
        canvas_size = 100
        points = get_triangle_points(6, 8, 10, canvas_size=canvas_size)
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        
        # X or Y
        touches_x = (min(xs) == 0 and max(xs) == canvas_size)
        touches_y = (min(ys) == 0 and max(ys) == canvas_size)
        self.assertTrue(touches_x or touches_y)

    # Types and float precision
    
    def test_precision_very_small_triangle(self):
        # 27 very small triangle
        points = get_triangle_points(0.0003, 0.0004, 0.0005, canvas_size=100)
        xs = [p[0] for p in points]
        self.assertEqual(max(xs), 100)

    def test_precision_huge_triangle(self):
        # 18 very big triangle
        points = get_triangle_points(3e6, 4e6, 5e6, canvas_size=100)
        xs = [p[0] for p in points]
        self.assertEqual(max(xs), 100)

    def test_output_format_is_integer_tuples(self):
        # 19 output for drawing on a canvas must be int
        points = get_triangle_points(3, 4, 5, 100)
        for p in points:
            self.assertIsInstance(p, tuple)
            self.assertIsInstance(p[0], int)
            self.assertIsInstance(p[1], int)

    def test_order_of_returned_points(self):
        # 20 Check for offset (offset_x, offset_y).
        canvas_size = 100
        points = get_triangle_points(5, 5, 5, canvas_size=canvas_size)
        
        # Unilateral: w = 5, h = 5 * sin(pi/3) = 4.3301
        tri_w = 5.0
        tri_h = 5.0 * math.sin(math.pi / 3)
        scale = min(canvas_size / tri_w, canvas_size / tri_h) # scale по h
        
        expected_offset_x = (canvas_size - (tri_w * scale)) / 2.0
        expected_offset_y = (canvas_size - (tri_h * scale)) / 2.0
        
        first_point = points[0]
        self.assertEqual(first_point[0], round(expected_offset_x))
        self.assertEqual(first_point[1], round(expected_offset_y))


if __name__ == "__main__":
    unittest.main()
