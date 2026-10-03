import logging
import math
import sys

from dataclasses import dataclass
from typing import Optional, Protocol

import sqlite3
import json

# Logger init
logger = logging.getLogger(__name__)

@dataclass
class Triangle:
    """Data model for Triangle"""
    side_a: float
    side_b: float
    side_c: float
    id: Optional[int] = None

class TriangleRepository:
    """Repository for SQLite database operations"""
    
    def __init__(self, db_name: str = "triangles.db"):
        """По умолчанию используется рабочая база данных, но её можно переопределить."""
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

class TriangleValidationError(Exception):
    """Custom exception raised when side dimensions violate basic geometry rules."""
    pass

class TraingleCalculate:
    """Service layer responsible for geometric computations."""
    
    @staticmethod  
    def get_triangle_points(triangle: Triangle, canvas_size: int = 100) -> list[tuple[int, int]]:
        # Unpack variables first to prevent NameError in logging
        a, b, c = triangle.side_a, triangle.side_b, triangle.side_c
        
        logger.info(
            f"Initializing triangle | Sides: a={a}, b={b}, c={c} | Canvas: {canvas_size}px"
        )
        
        # Exceptions are not caught here - catch them in main
        TraingleCalculate._validate_geometry(a, b, c)
        raw_points = TraingleCalculate._get_raw_points(a, b, c)
        points = TraingleCalculate._map_to_canvas(raw_points, canvas_size)
        return points

    @staticmethod
    def _validate_geometry(a: float, b: float, c: float) -> None:
        """Validates if the given sides can form a valid triangle"""
        if (a + b <= c) or (a + c <= b) or (b + c <= a):
            logger.error(f"Geometric Rule Violation: Sides [{a}, {b}, {c}] cannot form a triangle.")
            raise TriangleValidationError(f"Sides [{a}, {b}, {c}] cannot form a triangle.")
        logger.debug("Core geometric validation rules passed successfully.")

    @staticmethod
    def _get_raw_points(a: float, b: float, c: float) -> list[tuple[float, float]]:
        """Calculates raw geometric coordinates based on the law of cosines"""
        logger.debug("Calculating base angle A...")
        cos_A = (b**2 + c**2 - a**2) / (2 * b * c)
        angle_A = math.acos(cos_A)
        logger.debug(f"Calculated base angle A: {angle_A:.4f} rad")

        # Define points relative to the origin
        x1, y1 = 0.0, 0.0
        x2, y2 = float(c), 0.0
        x3, y3 = b * math.cos(angle_A), b * math.sin(angle_A)

        raw_points = [(x1, y1), (x2, y2), (x3, y3)]
        logger.debug(f"Calculated raw geometric vector points: {raw_points}")
        return raw_points 

    @staticmethod
    def _map_to_canvas(raw_points: list[tuple[float, float]], canvas_size: int) -> list[tuple[int, int]]:
        """Scales and centers raw vector points to fit within the specified pixel canvas"""
        xs = [p[0] for p in raw_points]
        ys = [p[1] for p in raw_points]

        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        tri_w = max_x - min_x 
        tri_h = max_y - min_y

        # Determine scaling factors while preventing division by zero
        scale_x = canvas_size / tri_w if tri_w > 0 else 1
        scale_y = canvas_size / tri_h if tri_h > 0 else 1
        scale = min(scale_x, scale_y)

        # Calculate dimensions after scaling
        scaled_width = tri_w * scale
        scaled_height = tri_h * scale

        # Offsets to center the shape on the canvas
        offset_x = (canvas_size - scaled_width) / 2.0
        offset_y = (canvas_size - scaled_height) / 2.0

        # Map raw float coordinates to integer pixel points
        pixel_tuples = []
        for x, y in raw_points:
            pixel_x = round((x - min_x) * scale + offset_x)
            pixel_y = round((y - min_y) * scale + offset_y)
            pixel_tuples.append((pixel_x, pixel_y))

        return pixel_tuples

from typing import Protocol

class InputService(Protocol):
    """Like interface in cs"""
    def read(self, prompt: str) -> str:
        ...

class ConsoleInputService:
    def read(self, prompt: str) -> str:
        return input(prompt)

class MockInputService:
    def __init__(self, return_values: list[str]):
        # Turn list into iterator
        self.outputs = iter(return_values)
        
    def read(self, prompt: str) -> str:
        return next(self.outputs)

class TriangleInputHandler:
    def __init__(self, input_service: InputService):
        self.input_service = input_service

    def get_triangle(self) -> Triangle:
        while True:
            try:
                # Вместо жестко зашитого input() вызываем сервис
                side_a = float(self.input_service.read("Input side A length: "))
                side_b = float(self.input_service.read("Input side B length: "))
                side_c = float(self.input_service.read("Input side C length: "))
                
                if side_a <= 0 or side_b <= 0 or side_c <= 0:
                    print("Error: Side lengths must be greater than zero!")
                    continue
                    
                return Triangle(side_a, side_b, side_c)
            except ValueError:
                print("Error: Invalid number format.")

def main() -> None:
    log_format = "%(asctime)s | [%(levelname)-7s] | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=logging.DEBUG,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    logger.info("Logger started")
    
    TriangleRepository.init_db()
    
    main_triangle = TriangleInputHandler.get_triangle()
    
    try:
        # Calculate coordinates
        points = TraingleCalculate.get_triangle_points(main_triangle, canvas_size=100)
        print(f"\nCalculated Points:\n{points}")

        # Save to database
        db_id = TriangleRepository.save(main_triangle, points)
        print(f"Successfully saved to DB (ID: {db_id})")

        # Read it back from the DB
        print("\n--- Reading back from Database Verification ---")
        loaded_triangle, loaded_points = TriangleRepository.get_by_id(db_id)
        print(f"Loaded object: {loaded_triangle}")
        print(f"Loaded points: {loaded_points}")

    except TriangleValidationError as tri_ex:
        logger.error(f"Aborted: Geometry parameters broken. Details: {tri_ex}")
        print(f"\nGeometry Error: These dimensions cannot form a physical triangle.")

if __name__ == "__main__":
    main()
