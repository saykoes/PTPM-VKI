import sqlite3
import json
import logging

from Triangle import Triangle
from typing import Optional

logger = logging.getLogger(__name__)

class TriangleRepository:
    """Repository for SQLite database operations"""
    
    def __init__(self, db_name: str = "triangles.db"):
        self.db_name = db_name

    def init_db(self) -> None:
        """Creates the necessary tables if they do not exist"""
        logger.info("Initializing database...")
        # Using a context manager 'with' automatically closes the connection
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS triangles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    side_a REAL NOT NULL,
                    side_b REAL NOT NULL,
                    side_c REAL NOT NULL,
                    pixel_points TEXT
                )
            """)
            conn.commit()
        logger.debug("Database table initialized successfully")

    def save(self, triangle: Triangle, pixel_points: list[tuple[int, int]]) -> int:
        """Saves a triangle and its calculated points to the db
        
        Returns the inserted row ID
        """
        logger.info(f"Saving triangle to database: {triangle}")
        
        # Serialize the list of tuples into a JSON string to put them inside TEXT field
        serialized_points = json.dumps(pixel_points)

        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO triangles (side_a, side_b, side_c, pixel_points)
                VALUES (?, ?, ?, ?)
                """,
                (triangle.side_a, triangle.side_b, triangle.side_c, serialized_points)
            )
            conn.commit()
            
            # Get the auto-incremented ID assigned by SQLite
            triangle.id = cursor.lastrowid
            logger.info(f"Triangle successfully saved with ID: {triangle.id}")
            return triangle.id

    def get_by_id(self, triangle_id: int) -> tuple[Optional[Triangle], Optional[list[tuple[int, int]]]]:
        """Retrieves a triangle and its points by ID from the db"""
        logger.info(f"Fetching triangle (ID: {triangle_id}) from db...")
        
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, side_a, side_b, side_c, pixel_points FROM triangles WHERE id = ?",
                (triangle_id,)
            )
            row = cursor.fetchone()

        if not row:
            logger.warning(f"Triangle (ID: {triangle_id}) not found")
            return None, None

        # Make Triangle object
        triangle = Triangle(id=row[0], side_a=row[1], side_b=row[2], side_c=row[3])
        # Deserialize JSON string back
        raw_points = json.loads(row[4])
        pixel_points = [tuple(p) for p in raw_points]

        logger.info(f"Successfully loaded triangle: {triangle}")
        return triangle, pixel_points
    
    def get_by_sides(self, a: float, b: float, c: float) -> tuple[Optional[Triangle], Optional[list[tuple[int, int]]]]:
        """Searches the database for an existing triangle with matching side dimensions."""
        logger.info(f"Checking DB cache for triangle sides: a={a}, b={b}, c={c}...")
        
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            # Ищем точное совпадение по всем трем сторонам
            cursor.execute(
                """
                SELECT id, side_a, side_b, side_c, pixel_points 
                FROM triangles 
                WHERE side_a = ? AND side_b = ? AND side_c = ?
                """,
                (a, b, c)
            )
            row = cursor.fetchone()

        if not row:
            logger.debug("No matching triangle cached in the database.")
            return None, None

        # Собираем объект Triangle и десериализуем JSON-точки точно так же, как в get_by_id
        triangle = Triangle(id=row[0], side_a=row[1], side_b=row[2], side_c=row[3])
        raw_points = json.loads(row[4])
        pixel_points = [tuple(p) for p in raw_points]

        logger.info(f"Cache hit! Found existing cached triangle with ID: {triangle.id}")
        return triangle, pixel_points
