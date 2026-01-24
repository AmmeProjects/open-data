"""
Shared data types for the data loading module.
"""

from dataclasses import dataclass


@dataclass
class LocationInfo:
    """Metadata about a charging location from OCPI."""

    id: str
    name: str
    address: str
    city: str
    postal_code: str
    country: str
    latitude: float
    longitude: float
    operator: str
    party_id: str
