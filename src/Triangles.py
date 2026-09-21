import logging
import math
import sys

logger = logging.getLogger(__name__)

class TriangleValidationError(Exception):
    #Custom exception raised when side dimensions violate basic geometry rules.
    pass

def convert_float(str_conv: str) -> float:
    logger.debug(f"Converting string input: '{str_conv}'...")
    try:
        result = float(str_conv)
        logger.debug(f"Successfully converted '{str_conv}' -> float: {result}")
        return result
    except ValueError as ex:
        logger.exception(
            f"Error: Cannot convert '{str_conv}' into a number."
        )
        # Re-raise the exception to inform the caller
        raise ValueError(
            f"Invalid float: '{str_conv}'"
        ) from ex

def get_triangle_points(a: float, b: float, c: float, canvas_size: int = 100) -> list[tuple[int,int]]:

    logger.info(
        f"Initializing triangle | Sides: a={a}, b={b}, c={c} | Canvas: {canvas_size}px"
    )

    # Geometry Validation
    if (a + b <= c) or (a + c <= b) or (b + c <= a):
        logger.error(
            f"Geometric Rule Violation: Sides [{a}, {b}, {c}] cannot form a triangle."
        )
        raise TriangleValidationError(
            f"Sides [{a}, {b}, {c}] cannot form a triangle."
        )

    logger.debug("Core geometric validation rules passed successfully.")

    # Trigonometry (law of cosines)
    # AB = side c (Flat along baseline x-axis)
    # AC = side b
    # BC = side a
    logger.debug("Calculating base angle A...")
    cos_A = (b**2 + c**2 - a**2) / (2 * b * c)
    angle_A = math.acos(cos_A)
    logger.debug(
        f"Calculated base angle A: {angle_A:.4f} radians ({math.degrees(angle_A):.2f}°)"
    )

    # Coordinates relative to origin
    x1, y1 = 0.0, 0.0
    x2, y2 = float(c), 0.0
    x3, y3 = b * math.cos(angle_A), b * math.sin(angle_A)

    raw_points = [(x1, y1), (x2, y2), (x3, y3)]
    logger.debug(f"Calculated raw geometric vector points: {raw_points}")

    # Because some triangles (like obtuse triangles) shift backward into negative space 
    # we need to find bounding box of a triangle separately
    xs = []
    ys = []
    
    for p in raw_points:
        xs.append(p[0])
        ys.append(p[1])

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    tri_w = max_x - min_x 
    tri_h = max_y - min_y
    logger.debug(
        f"Raw bounding box established - Width: {tri_w:.4f}, Height: {tri_h:.4f}"
    )

    # Determine scaling factor (Aspect ratio Fit)
    scale_x = canvas_size / tri_w
    scale_y = canvas_size / tri_h

    # Take the smaller multiplier to fit the whole triangle inside the frame
    scale = min(scale_x, scale_y)

    # Calculate Centering Offsets
    # Determine dimensions after scaling
    scaled_width = tri_w * scale
    scaled_height = tri_h * scale

    # Find the remainder space on the canvas and split it evenly to center the shape
    offset_x = (canvas_size - scaled_width) / 2.0
    offset_y = (canvas_size - scaled_height) / 2.0

    logger.debug(
        f"Scale profile matched: {scale:.4f} | Canvas offsets: X={offset_x:.2f}, Y={offset_y:.2f}"
    )

    # Map raw coordinates down to integer pixel points
    pixel_tuples = []
    for x, y in raw_points:
        pixel_x: int = round((x - min_x) * scale + offset_x)
        pixel_y: int = round((y - min_y) * scale + offset_y)
        pixel_tuples.append((pixel_x, pixel_y))

    logger.info(
        f"Successfully generated canvas pixel coordinates: {pixel_tuples}"
    )
    return pixel_tuples


def main():
    log_format = "%(asctime)s | [%(levelname)-7s] | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=logging.DEBUG,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("logs/file_txt.log", encoding="utf-8"),
        ],
    )

    logger.info("Logger started")

    try:
        raw_a = input("Input side A length: ")
        side_a = convert_float(raw_a)

        raw_b = input("Input side B length: ")
        side_b = convert_float(raw_b)

        raw_c = input("Input side C length: ")
        side_c = convert_float(raw_c)

        points = get_triangle_points(side_a, side_b, side_c)
        print(f"\nResult:\n{points}")

    except ValueError as val_ex:
        logger.critical(
            f"Aborted: Input failure: {val_ex}"
        )
        return

    except TriangleValidationError as tri_ex:
        logger.error(
            f"Aborted: Geometry parameters broken. Details: {tri_ex}"
        )
        return

    logger.info("Program is executed successfuly")

if __name__ == "__main__":
    main()