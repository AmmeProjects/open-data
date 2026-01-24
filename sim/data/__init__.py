"""
OCPI data loader for charging location and EVSE information.

This module loads and parses OCPI (Open Charge Point Interface) format data
from locations.json files to create Charger models for simulation.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from sim.models.charger import Charger, ChargerType
from sim.data.registry import ChargerRegistry, ChargerEntry
from sim.data.types import LocationInfo


def map_ocpi_standard_to_connector_type(standard: str) -> str:
    """
    Map OCPI connector standard to our connector type naming.

    Args:
        standard: OCPI standard like 'IEC_62196_T2', 'IEC_62196_T2_COMBO', 'CHADEMO'

    Returns:
        Connector type string like 'Type2', 'CCS', 'CHAdeMO'
    """
    mapping = {
        "IEC_62196_T2": "Type2",
        "IEC_62196_T2_COMBO": "CCS",
        "CHADEMO": "CHAdeMO",
        "IEC_60309_2_single_16": "Type2",  # Industrial connector, treat as Type2
    }
    return mapping.get(standard, standard)


def map_ocpi_power_type(power_type: str) -> ChargerType:
    """
    Map OCPI power type to ChargerType enum.

    Args:
        power_type: OCPI power type like 'AC_1_PHASE', 'AC_3_PHASE', 'DC'

    Returns:
        ChargerType.AC or ChargerType.DC
    """
    if power_type == "DC":
        return ChargerType.DC
    else:  # AC_1_PHASE or AC_3_PHASE
        return ChargerType.AC


def get_phases_from_power_type(power_type: str) -> int:
    """
    Extract number of phases from OCPI power type.

    Args:
        power_type: OCPI power type like 'AC_1_PHASE', 'AC_3_PHASE', 'DC'

    Returns:
        Number of phases (1 or 3, defaults to 3 for DC)
    """
    if power_type == "AC_1_PHASE":
        return 1
    else:  # AC_3_PHASE or DC
        return 3


def create_charger_from_connector(
    connector_data: Dict,
    evse_data: Dict,
    location_info: LocationInfo,
) -> Charger:
    """
    Create a Charger model from OCPI connector data.

    Args:
        connector_data: OCPI connector dictionary
        evse_data: OCPI EVSE dictionary (parent of connector)
        location_info: Location metadata

    Returns:
        Charger instance
    """
    # Extract connector properties
    standard = connector_data["standard"]
    power_type = connector_data["power_type"]
    max_voltage = connector_data["max_voltage"]
    max_amperage = connector_data["max_amperage"]
    max_power_w = connector_data["max_electric_power"]

    # Convert to our models
    connector_type = map_ocpi_standard_to_connector_type(standard)
    charger_type = map_ocpi_power_type(power_type)
    phases = get_phases_from_power_type(power_type)
    max_power_kw = max_power_w / 1000.0

    # Create charger name
    power_str = (
        f"{max_power_kw:.0f}kW" if max_power_kw < 100 else f"{max_power_kw:.0f}kW"
    )
    name = f"{location_info.operator} - {location_info.city} ({connector_type} {power_str})"

    return Charger(
        name=name,
        charger_type=charger_type,
        connector_type=connector_type,
        max_voltage=float(max_voltage),
        max_current=float(max_amperage),
        max_power_kw=max_power_kw,
        phases=phases,
    )


def load_ocpi_locations(file_path: str) -> List[Dict]:
    """
    Load OCPI locations from JSON file.

    Args:
        file_path: Path to locations.json file

    Returns:
        List of location dictionaries

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"OCPI locations file not found: {file_path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("data", [])


def parse_ocpi_location(
    location_data: Dict,
) -> Tuple[LocationInfo, List[Tuple[Dict, Dict]]]:
    """
    Parse a single OCPI location to extract metadata and connectors.

    Args:
        location_data: OCPI location dictionary

    Returns:
        Tuple of (LocationInfo, list of (evse_data, connector_data) tuples)
    """
    # Extract location metadata
    coords = location_data["coordinates"]
    location_info = LocationInfo(
        id=location_data["id"],
        name=location_data["name"],
        address=location_data["address"],
        city=location_data["city"],
        postal_code=location_data["postal_code"],
        country=location_data["country"],
        latitude=coords["latitude"],
        longitude=coords["longitude"],
        operator=location_data["operator"],
        party_id=location_data["party_id"],
    )

    # Extract all connectors from all EVSEs
    connectors = []
    for evse in location_data.get("evses", []):
        for connector in evse.get("connectors", []):
            connectors.append((evse, connector))

    return location_info, connectors


def load_chargers_from_ocpi(
    file_path: str,
    filter_operator: Optional[str] = None,
    filter_city: Optional[str] = None,
    filter_power_type: Optional[str] = None,
) -> List[Tuple[Charger, LocationInfo, str]]:
    """
    Load chargers from OCPI locations file with optional filtering.

    Args:
        file_path: Path to locations.json file
        filter_operator: Optional operator name to filter by
        filter_city: Optional city name to filter by
        filter_power_type: Optional power type to filter by ('AC' or 'DC')

    Returns:
        List of tuples (Charger, LocationInfo, connector_id)

    Example:
        >>> chargers = load_chargers_from_ocpi(
        ...     'data/naps/portugal/locations.json',
        ...     filter_city='Lisboa',
        ...     filter_power_type='DC'
        ... )
        >>> print(f"Found {len(chargers)} DC chargers in Lisboa")
    """
    locations = load_ocpi_locations(file_path)

    result = []
    for location_data in locations:
        # Apply location-level filters
        if filter_operator and location_data["operator"] != filter_operator:
            continue
        if filter_city and location_data["city"] != filter_city:
            continue

        location_info, connectors = parse_ocpi_location(location_data)

        for evse_data, connector_data in connectors:
            # Apply connector-level filters
            if filter_power_type:
                connector_type = map_ocpi_power_type(connector_data["power_type"])
                if (
                    filter_power_type.upper() == "AC"
                    and connector_type != ChargerType.AC
                ):
                    continue
                if (
                    filter_power_type.upper() == "DC"
                    and connector_type != ChargerType.DC
                ):
                    continue

            charger = create_charger_from_connector(
                connector_data, evse_data, location_info
            )
            result.append((charger, location_info, connector_data["id"]))

    return result


def get_charger_statistics(file_path: str) -> Dict:
    """
    Get statistics about chargers in the OCPI data.

    Args:
        file_path: Path to locations.json file

    Returns:
        Dictionary with statistics
    """
    locations = load_ocpi_locations(file_path)

    stats = {
        "total_locations": len(locations),
        "total_evses": 0,
        "total_connectors": 0,
        "by_operator": {},
        "by_city": {},
        "by_power_type": {"AC": 0, "DC": 0},
        "by_connector_type": {},
        "power_range": {"min_kw": float("inf"), "max_kw": 0},
    }

    for location in locations:
        operator = location["operator"]
        city = location["city"]

        stats["by_operator"][operator] = stats["by_operator"].get(operator, 0) + 1
        stats["by_city"][city] = stats["by_city"].get(city, 0) + 1

        for evse in location.get("evses", []):
            stats["total_evses"] += 1

            for connector in evse.get("connectors", []):
                stats["total_connectors"] += 1

                power_type = connector["power_type"]
                charger_type = "DC" if power_type == "DC" else "AC"
                stats["by_power_type"][charger_type] += 1

                connector_type = map_ocpi_standard_to_connector_type(
                    connector["standard"]
                )
                stats["by_connector_type"][connector_type] = (
                    stats["by_connector_type"].get(connector_type, 0) + 1
                )

                power_kw = connector["max_electric_power"] / 1000.0
                stats["power_range"]["min_kw"] = min(
                    stats["power_range"]["min_kw"], power_kw
                )
                stats["power_range"]["max_kw"] = max(
                    stats["power_range"]["max_kw"], power_kw
                )

    return stats


__all__ = [
    "LocationInfo",
    "load_ocpi_locations",
    "load_chargers_from_ocpi",
    "get_charger_statistics",
    "create_charger_from_connector",
    "parse_ocpi_location",
    "ChargerRegistry",
    "ChargerEntry",
]
