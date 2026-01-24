"""
Charger registry for querying real-world charging infrastructure.

This module provides a registry for loading and querying chargers from OCPI data,
making it easy to find chargers by location, operator, power type, etc.
"""

from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass
import math

from sim.models.charger import Charger, ChargerType
from sim.data.types import LocationInfo


@dataclass
class ChargerEntry:
    """A charger with its associated metadata."""

    charger: Charger
    location: LocationInfo
    connector_id: str
    evse_uid: Optional[str] = None

    def __repr__(self) -> str:
        return (
            f"ChargerEntry({self.charger.name}, "
            f"{self.location.city}, {self.charger.max_power_kw}kW)"
        )


class ChargerRegistry:
    """
    Registry for querying charging infrastructure from OCPI data.

    This class loads OCPI data and provides convenient query methods
    to find chargers by various criteria.

    Example:
        >>> registry = ChargerRegistry('data/naps/portugal/locations.json')
        >>> lisboa_dc = registry.find_by_city_and_type('Lisboa', 'DC')
        >>> print(f"Found {len(lisboa_dc)} DC chargers in Lisboa")
    """

    def __init__(self, ocpi_file_path: str):
        """
        Initialize the registry by loading OCPI data.

        Args:
            ocpi_file_path: Path to OCPI locations.json file
        """
        self.file_path = ocpi_file_path
        self._entries: List[ChargerEntry] = []
        self._load_data()

    def _load_data(self):
        """Load all chargers from OCPI file."""
        # Import here to avoid circular dependency
        from sim.data import load_chargers_from_ocpi

        charger_tuples = load_chargers_from_ocpi(self.file_path)

        for charger, location, connector_id in charger_tuples:
            entry = ChargerEntry(
                charger=charger,
                location=location,
                connector_id=connector_id,
            )
            self._entries.append(entry)

    @property
    def count(self) -> int:
        """Total number of chargers in registry."""
        return len(self._entries)

    def get_all(self) -> List[ChargerEntry]:
        """Get all charger entries."""
        return self._entries.copy()

    def find_by_city(self, city: str) -> List[ChargerEntry]:
        """
        Find all chargers in a specific city.

        Args:
            city: City name (case-sensitive)

        Returns:
            List of ChargerEntry objects
        """
        return [e for e in self._entries if e.location.city == city]

    def find_by_operator(self, operator: str) -> List[ChargerEntry]:
        """
        Find all chargers by operator name.

        Args:
            operator: Operator name (case-sensitive)

        Returns:
            List of ChargerEntry objects
        """
        return [e for e in self._entries if e.location.operator == operator]

    def find_by_type(self, charger_type: str) -> List[ChargerEntry]:
        """
        Find all chargers by type (AC or DC).

        Args:
            charger_type: 'AC' or 'DC'

        Returns:
            List of ChargerEntry objects
        """
        target_type = ChargerType.AC if charger_type.upper() == "AC" else ChargerType.DC
        return [e for e in self._entries if e.charger.charger_type == target_type]

    def find_by_city_and_type(self, city: str, charger_type: str) -> List[ChargerEntry]:
        """
        Find chargers in a specific city of a specific type.

        Args:
            city: City name
            charger_type: 'AC' or 'DC'

        Returns:
            List of ChargerEntry objects
        """
        target_type = ChargerType.AC if charger_type.upper() == "AC" else ChargerType.DC
        return [
            e
            for e in self._entries
            if e.location.city == city and e.charger.charger_type == target_type
        ]

    def find_by_power_range(
        self,
        min_power_kw: Optional[float] = None,
        max_power_kw: Optional[float] = None,
    ) -> List[ChargerEntry]:
        """
        Find chargers within a power range.

        Args:
            min_power_kw: Minimum power in kW (inclusive)
            max_power_kw: Maximum power in kW (inclusive)

        Returns:
            List of ChargerEntry objects
        """
        result = []
        for e in self._entries:
            power = e.charger.max_power_kw
            if min_power_kw is not None and power < min_power_kw:
                continue
            if max_power_kw is not None and power > max_power_kw:
                continue
            result.append(e)
        return result

    def find_fast_chargers(self, min_power_kw: float = 50.0) -> List[ChargerEntry]:
        """
        Find fast chargers (typically DC >= 50kW).

        Args:
            min_power_kw: Minimum power to be considered "fast" (default 50kW)

        Returns:
            List of ChargerEntry objects
        """
        return [
            e
            for e in self._entries
            if e.charger.charger_type == ChargerType.DC
            and e.charger.max_power_kw >= min_power_kw
        ]

    def find_nearby(
        self,
        latitude: float,
        longitude: float,
        max_distance_km: float = 10.0,
    ) -> List[Tuple[ChargerEntry, float]]:
        """
        Find chargers near a specific location.

        Args:
            latitude: Latitude in degrees
            longitude: Longitude in degrees
            max_distance_km: Maximum distance in kilometers

        Returns:
            List of tuples (ChargerEntry, distance_km) sorted by distance
        """
        from math import radians, cos, sin, asin, sqrt

        def haversine(lat1, lon1, lat2, lon2):
            """Calculate distance between two points on Earth in km."""
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
            c = 2 * asin(sqrt(a))
            km = 6371 * c  # Earth radius in km
            return km

        results = []
        for e in self._entries:
            distance = haversine(
                latitude, longitude, e.location.latitude, e.location.longitude
            )
            if distance <= max_distance_km:
                results.append((e, distance))

        # Sort by distance
        results.sort(key=lambda x: x[1])
        return results

    def get_cities(self) -> List[str]:
        """Get list of unique cities with chargers."""
        return sorted(set(e.location.city for e in self._entries))

    def get_operators(self) -> List[str]:
        """Get list of unique operators."""
        return sorted(set(e.location.operator for e in self._entries))

    def get_statistics(self) -> Dict:
        """Get comprehensive statistics about the registry."""
        # Import here to avoid circular dependency
        from sim.data import get_charger_statistics

        return get_charger_statistics(self.file_path)

    def summary(self) -> str:
        """Generate a human-readable summary of the registry."""
        stats = self.get_statistics()

        summary = f"""
Charger Registry Summary
========================
Total locations:  {stats["total_locations"]}
Total EVSEs:      {stats["total_evses"]}
Total connectors: {stats["total_connectors"]}

By Type:
--------
AC chargers:  {stats["by_power_type"]["AC"]}
DC chargers:  {stats["by_power_type"]["DC"]}

Power Range:
------------
Minimum: {stats["power_range"]["min_kw"]:.1f} kW
Maximum: {stats["power_range"]["max_kw"]:.1f} kW

Top 10 Operators:
-----------------"""

        top_operators = sorted(
            stats["by_operator"].items(), key=lambda x: x[1], reverse=True
        )[:10]

        for operator, count in top_operators:
            summary += f"\n  {operator:<40} {count:>4} locations"

        summary += "\n\nTop 10 Cities:\n"
        summary += "-" * 50

        top_cities = sorted(stats["by_city"].items(), key=lambda x: x[1], reverse=True)[
            :10
        ]

        for city, count in top_cities:
            summary += f"\n  {city:<40} {count:>4} locations"

        return summary

    def __len__(self) -> int:
        """Return number of chargers in registry."""
        return len(self._entries)

    def __repr__(self) -> str:
        return f"ChargerRegistry({len(self._entries)} chargers)"


__all__ = [
    "ChargerEntry",
    "ChargerRegistry",
]
