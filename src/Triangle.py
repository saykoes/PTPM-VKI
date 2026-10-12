from dataclasses import dataclass
from typing import Optional

@dataclass
class Triangle:
    """Data model for Triangle"""
    side_a: float
    side_b: float
    side_c: float
    id: Optional[int] = None