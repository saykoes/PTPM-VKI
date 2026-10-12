import unittest
from unittest.mock import patch, MagicMock

from TInput import TriangleInputHandler, MockInputService, ConsoleInputService

class TestTriangleInputHandler(unittest.TestCase):
    
    def test_input_via_di(self):
        # The stream of inputs:
        # Loop 1: 'invalid_string' crashes on side_a format validation.
        # Loop 2: Read side_a='-5', side_b='3', side_c='4'. 
        #         Fails 'side <= 0' check because of side_a -> loop resets.
        # Loop 3: Read side_a='5', side_b='6', side_c='7'. Valid inputs!
        fake_input = MockInputService(['invalid_string', '-5', '3', '4', '5', '6', '7', '8'])
        
        mock_calc = MagicMock()
        mock_calc.get_triangle_points.return_value = [(0, 0), (5, 0), (0, 6)]
        
        handler = TriangleInputHandler(
            input_service=fake_input,
            repository=MagicMock(),
            calculator=MagicMock()
        )
        
        handler._find_existing_in_db = MagicMock(return_value=(None, None))
        
        triangle, _ = handler.run_flow()
        self.assertIsNotNone(triangle)
        
    def test_input_via_patch(self):
        # patches the input()
        # side_effect gives values in order 
        with patch('builtins.input', side_effect=['3', '4', '5']):
            # any input() requset here will given the mock values automatically
            service = ConsoleInputService()
            handler = TriangleInputHandler(
                input_service=service,
                repository=MagicMock(),
                calculator=MagicMock()
            )
            
            handler._find_existing_in_db = MagicMock(return_value=(None, None))

            triangle, _ = handler.run_flow()
            
        self.assertEqual(triangle.side_a, 3.0)
