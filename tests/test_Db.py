import unittest
from unittest.mock import patch, MagicMock

import sqlite3

from Triangle import Triangle
from TRepository import TriangleRepository
from TCalculate import TriangleCalculate
from TInput import TriangleInputHandler, MockInputService

class TestRepositoryUnitMock(unittest.TestCase):

    @patch("TRepository.sqlite3.connect")
    def test_get_by_id_unit(self, mock_connect):
        # now sqlite3.connect = mock_connect
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        mock_connect.return_value = mock_conn
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Immitate the db (id, len1,len2,len3, pixel_points)
        mock_cursor.fetchone.return_value = (1, 3.0, 4.0, 5.0, '[[0,0],[3,0],[0,4]]')

        # real repo, fake db
        repo = TriangleRepository(db_name="fake.db")
        triangle, points = repo.get_by_id(1)

        # Assert the right sql query
        mock_cursor.execute.assert_called_once_with(
            "SELECT id, side_a, side_b, side_c, pixel_points FROM triangles WHERE id = ?",
            (1,) #triangle id
        )
        
        self.assertIsNotNone(triangle)
        self.assertEqual(triangle.side_a, 3.0)

class TestTriangleIntegration(unittest.TestCase):
    """Integration tests: Verifies component interactions and SQLite operations."""

    def setUp(self):
        """Initializes a shared in-memory connection and hooks it into the repository."""
        # Create shared connection (because :memory: db only lives under one connection)
        self.shared_conn = sqlite3.connect(":memory:")
        
        # Patch sqlite connect, so that it will use shared connection instead
        self.patcher = patch("TRepository.sqlite3.connect", return_value=self.shared_conn)
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
        
        handler = TriangleInputHandler(
            input_service=fake_input,
            repository=self.repo,
            calculator=TriangleCalculate
        )
        
        triangle, points = handler.run_flow(canvas_size=200)

        self.assertIsNotNone(triangle)
        self.assertEqual(triangle.side_a, 5.0)
        self.assertEqual(len(points), 3)
