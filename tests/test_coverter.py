import unittest
from converter import Converter

class TestConverter(unittest.TestCase):
    def test_do_big(self):
        border = Converter.do(100.7)
        self.assertEqual(border, 1000)
        
        flt = Converter.do(2000.7)
        self.assertEqual(flt, 1000)
    
    def test_do_pos(self):
        border_up = Converter.do(100.6)
        self.assertEqual(border_up, 100)
        
        border_down = Converter.do(0.1)
        self.assertEqual(border_down, 0)
        
        flt = Converter.do(45.6)
        self.assertEqual(flt, 45)
        
    def test_do_zero(self):
        with self.assertRaises(ValueError):
            Converter.do(0)
    
    def test_do_neg(self):
        border_up = Converter.do(-0.1)
        self.assertEqual(border_up, -5)
        
        border_down = Converter.do(-30.4)
        self.assertEqual(border_down, -35)
        
    def test_do_border_neg(self):
        with self.assertRaises(ValueError):
            Converter.do(-30.45)
    
    def test_do_small(self):
        border_up = Converter.do(-30.5)
        self.assertEqual(border_up,-2000)
        
        flt = Converter.do(-340)
        self.assertEqual(flt, -2000)
