import logging
import sys

from TRepository import TriangleRepository
from TCalculate import TriangleValidationError, TriangleCalculate
from TInput import TriangleInputHandler,ConsoleInputService

# Logger init
logger = logging.getLogger(__name__)

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
    
    repo = TriangleRepository(db_name="triangles.db")
    repo.init_db()
    input_service = ConsoleInputService()
    
    handler = TriangleInputHandler(
        input_service=input_service,
        repository=repo,
        calculator=TriangleCalculate
    )
    
    try:
        logger.info("\n--- Starting Application Flow ---")
        
        final_triangle, final_points = handler.run_flow(canvas_size=100)
        
        print("\n--- Flow Execution Summary ---")
        print(f"Resulting Triangle: {final_triangle}")
        print(f"Resulting Points:   {final_points}")

    except TriangleValidationError as tri_ex:
        logger.error(f"Aborted: Geometry parameters broken. Details: {tri_ex}")
        print(f"\nGeometry Error: These dimensions cannot form a physical triangle.")

if __name__ == "__main__":
    main()