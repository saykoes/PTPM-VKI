import unittest
from unittest.mock import patch
import sqlite3

from Triangles import (
    Triangle, 
    TriangleRepository, 
    TriangleCalculate, 
    TriangleValidationError, 
    TriangleInputHandler,
    ConsoleInputService,
    MockInputService
)

class TestTriangleIntegration(unittest.TestCase):
    """Integration tests: Verifies component interactions and SQLite operations."""

    def setUp(self):
        """Initializes a shared in-memory connection and hooks it into the repository."""
        # Create shared connection (because :memory: db only lives under one connection)
        self.shared_conn = sqlite3.connect(":memory:")
        
        # Patch sqlite connect, so that it will use shared connection instead
        self.patcher = patch("sqlite3.connect", return_value=self.shared_conn)
        self.mock_connect = self.patcher.start()

        self.repo = TriangleRepository(db_name=":memory:")
        self.repo.init_db()
        
    def tearDown(self):
        """Stops the patcher and closes the shared connection safely."""
        # Close shared connection (db is now purged)
        self.shared_conn.close()
        # Unpatch sqlite connect
        self.patcher.stop()

    def test_integration_db_save_and_retrieve(self):
        """Test 1. CRUD operations"""
        triangle = Triangle(6.0, 8.0, 10.0)
        mock_points = [(0, 0), (50, 0), (25, 45)]
        
        # Save data to the db
        inserted_id = self.repo.save(triangle, mock_points)
        self.assertIsNotNone(inserted_id)
        
        # Retrieve data back from the db
        db_triangle, db_points = self.repo.get_by_id(inserted_id)
        
        # Check data integrity after passing through db
        self.assertEqual(db_triangle.side_a, 6.0)
        self.assertEqual(db_points, mock_points)

    def test_integration_calculator_to_database(self):
        """Test 2. Component Chain: TriangleCalculate -> JSON Serializer -> Database"""
        triangle = Triangle(3.0, 4.0, 5.0)
        
        # Calculate points 
        calculated_points = TriangleCalculate.get_triangle_points(triangle, canvas_size=100)
        
        # Pass generated data to the repository to save it into db
        inserted_id = self.repo.save(triangle, calculated_points)
        
        # Fetch the data back
        _, db_points = self.repo.get_by_id(inserted_id)
        
        # Ensure data structures and types are preserved 
        self.assertEqual(len(db_points), 3)
        self.assertEqual(db_points, calculated_points)

    def test_integration_full_flow_end_to_end(self):
        """Test 3. Complete application lifecycle
        
        Input -> Handler -> Calculator -> Repository -> DB
        """
        # Mock user keyboard input 
        fake_input = MockInputService(['5.0', '5.0', '5.0'])
        handler = TriangleInputHandler(input_service=fake_input)
        
        # Get triangle sides
        triangle = handler.get_triangle()
        
        # Pass to the calculator
        points = TriangleCalculate.get_triangle_points(triangle, canvas_size=200)
        
        # Save to db
        inserted_id = self.repo.save(triangle, points)
        
        # Get from db
        db_triangle, db_points = self.repo.get_by_id(inserted_id)
        
        self.assertIsNotNone(db_triangle)
        self.assertEqual(db_triangle.side_a, 5.0)
        self.assertEqual(len(db_points), 3)


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

class TestTriangleInputHandler(unittest.TestCase):
    
    def test_input_via_di(self):
        # The stream of inputs:
        # Loop 1: 'invalid_string' crashes on side_a format validation.
        # Loop 2: Read side_a='-5', side_b='3', side_c='4'. 
        #         Fails 'side <= 0' check because of side_a -> loop resets.
        # Loop 3: Read side_a='5', side_b='6', side_c='7'. Valid inputs!
        fake_input = MockInputService(['invalid_string', '-5', '3', '4', '5', '6', '7', '8'])
        handler = TriangleInputHandler(input_service=fake_input)
        
        triangle = handler.get_triangle()
        
        # The correct data from the third successful loop iteration.
        self.assertEqual(triangle.side_a, 5.0)
        self.assertEqual(triangle.side_b, 6.0)
        self.assertEqual(triangle.side_c, 7.0)
        
    def test_input_via_patch(self):
        # patches the input()
        # side_effect gives values in order 
        with patch('builtins.input', side_effect=['3', '4', '5']):
            # any input() requset here will given the mock values automatically
            service = ConsoleInputService()
            handler = TriangleInputHandler(input_service=service)
            
            triangle = handler.get_triangle()
            
        self.assertEqual(triangle.side_a, 3.0)

if __name__ == '__main__':
    unittest.main()
