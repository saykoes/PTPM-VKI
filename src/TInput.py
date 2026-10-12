from typing import List, Protocol, Tuple, Optional
from Triangle import Triangle
import logging

logger = logging.getLogger(__name__)

class InputService(Protocol):
    """Like interface in csharp"""
    def read(self, prompt: str) -> str:
        # Abstract method
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
    def __init__(self, 
                 input_service: InputService, 
                 repository, 
                 calculator):
        
        self.input_service = input_service
        self.repository = repository
        self.calculator = calculator

    def run_flow(self, canvas_size: int = 100) -> Tuple[any, List[Tuple[int, int]]]:
        """Executes the complete application lifecycle sequence.
        
        Returns a tuple containing the Triangle object and its calculated pixel points.
        """
        
        triangle = self._get_valid_triangle_input()
        
        # Check if identical triangle dimensions already exist in the database cache
        db_triangle, db_points = self._find_existing_in_db(triangle)

        if db_triangle and db_points:
            # Data exists -> Reuse cache instead of calculating
            logger.info("[Controller] Record found in DB! Reusing cached coordinates.")
            final_triangle = db_triangle
            final_points = db_points
        else:
            # Data is unique -> Compute, format, and commit to DB
            logger.info("[Controller] No record in DB. Computing new coordinates and saving...")
            final_points = self.calculator.get_triangle_points(triangle, canvas_size=canvas_size)
            
            # Save new geometric calculations to the SQLite database
            inserted_id = self.repository.save(triangle, final_points)
            triangle.id = inserted_id
            final_triangle = triangle

        return final_triangle, final_points

    def _get_valid_triangle_input(self) -> any:
        """Helper retry loop to guarantee valid triangle size data entry."""
        while True:
            try:
                side_a = float(self.input_service.read("Input side A length: "))
                side_b = float(self.input_service.read("Input side B length: "))
                side_c = float(self.input_service.read("Input side C length: "))
                
                if side_a <= 0 or side_b <= 0 or side_c <= 0:
                    logger.error("Error: Side lengths must be greater than zero!")
                    continue
                    
                return Triangle(side_a, side_b, side_c)
            except ValueError:
                logger.error("Error: Invalid number format.")

    def _find_existing_in_db(self, target: any) -> Tuple[Optional[any], Optional[List[Tuple[int, int]]]]:
        """Helper querying interface to search database records by sides.
        
        Falls back to empty results gracefully if the repository lacks side matching.
        """
        if hasattr(self.repository, 'get_by_sides'):
            return self.repository.get_by_sides(target.side_a, target.side_b, target.side_c)
        return None, None