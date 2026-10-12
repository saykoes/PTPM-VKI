import logging
import math

from Triangle import Triangle

logger = logging.getLogger(__name__)

class TriangleValidationError(Exception):
    """Custom exception raised when side dimensions violate basic geometry rules."""
    pass

class TriangleCalculate:
    """Service layer responsible for geometric computations."""
    
    @staticmethod  
    def get_triangle_points(triangle: Triangle, canvas_size: int = 100) -> list[tuple[int, int]]:
        # Unpack variables first to prevent NameError in logging
        a, b, c = triangle.side_a, triangle.side_b, triangle.side_c
        
        logger.info(
            f"Initializing triangle | Sides: a={a}, b={b}, c={c} | Canvas: {canvas_size}px"
        )
        
        # Exceptions are not caught here - catch them in main
        TriangleCalculate._validate_geometry(a, b, c)
        raw_points = TriangleCalculate._get_raw_points(a, b, c)
        points = TriangleCalculate._map_to_canvas(raw_points, canvas_size)
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
