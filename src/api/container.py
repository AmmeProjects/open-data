from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class DataContainer:
    data: List | Dict | Any
    timestamp: str
    