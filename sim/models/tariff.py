"""
Tariff and pricing models for EV charging.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict


class TariffType(Enum):
    """Types of charging tariff components."""

    FLAT = "flat"  # Fixed fee per session
    ENERGY = "energy"  # Per kWh consumed
    TIME = "time"  # Per minute connected
    IDLE = "idle"  # Per minute after charging complete
    PARKING = "parking"  # Parking fee


@dataclass
class TariffComponent:
    """
    Individual tariff component.

    Attributes:
        type: TariffType (FLAT, ENERGY, TIME, IDLE, PARKING)
        rate: Amount in currency (e.g., EUR)
        unit: Unit of measurement ('session', 'kWh', 'minute', etc.)
    """

    type: TariffType
    rate: float
    unit: str

    def calculate(self, value: float) -> float:
        """
        Calculate cost for given usage value.

        Args:
            value: Usage amount (e.g., kWh, minutes, sessions)

        Returns:
            Cost in currency units
        """
        return self.rate * value

    def __repr__(self) -> str:
        return f"TariffComponent({self.type.value}: {self.rate} {self.unit})"


@dataclass
class Tariff:
    """
    Complete tariff structure for a charging location.

    This model supports the common Mobie tariff structure with:
    - Flat fee per session (activation/connection fee)
    - Energy-based pricing (per kWh)
    - Time-based pricing (per minute)
    - Idle fees (per minute after charging completes)
    - Parking fees (per minute)

    Attributes:
        id: Unique tariff identifier (e.g., connector UID from Mobie)
        operator: Charging operator name
        location_id: Optional location identifier
        connector_id: Optional specific connector identifier
        flat_fee: Fixed fee per charging session
        energy_rate: Price per kWh consumed
        time_rate: Price per minute connected
        idle_rate: Price per minute after charging completes
        parking_rate: Price per minute for parking
        currency: Currency code (default: EUR)
        valid_from: Optional start date of tariff validity
        valid_to: Optional end date of tariff validity
    """

    id: str
    operator: str
    location_id: Optional[str] = None
    connector_id: Optional[str] = None

    # Tariff rates
    flat_fee: float = 0.0
    energy_rate: float = 0.0
    time_rate: float = 0.0
    idle_rate: float = 0.0
    parking_rate: float = 0.0

    # Metadata
    currency: str = "EUR"
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None

    def __post_init__(self):
        """Validate tariff parameters."""
        if self.flat_fee < 0:
            raise ValueError(f"flat_fee must be non-negative, got {self.flat_fee}")
        if self.energy_rate < 0:
            raise ValueError(
                f"energy_rate must be non-negative, got {self.energy_rate}"
            )
        if self.time_rate < 0:
            raise ValueError(f"time_rate must be non-negative, got {self.time_rate}")
        if self.idle_rate < 0:
            raise ValueError(f"idle_rate must be non-negative, got {self.idle_rate}")
        if self.parking_rate < 0:
            raise ValueError(
                f"parking_rate must be non-negative, got {self.parking_rate}"
            )

    def calculate_cost(
        self,
        energy_kwh: float,
        time_minutes: float,
        idle_minutes: float = 0,
        parking_minutes: float = 0,
    ) -> float:
        """
        Calculate total cost for a charging session.

        Args:
            energy_kwh: Energy consumed in kWh
            time_minutes: Total connection time in minutes
            idle_minutes: Idle time after charging complete (minutes)
            parking_minutes: Parking time in minutes

        Returns:
            Total cost in specified currency
        """
        cost = (
            self.flat_fee
            + (energy_kwh * self.energy_rate)
            + (time_minutes * self.time_rate)
            + (idle_minutes * self.idle_rate)
            + (parking_minutes * self.parking_rate)
        )
        return cost

    def get_breakdown(
        self,
        energy_kwh: float,
        time_minutes: float,
        idle_minutes: float = 0,
        parking_minutes: float = 0,
    ) -> Dict[str, float]:
        """
        Get detailed cost breakdown by component.

        Args:
            energy_kwh: Energy consumed in kWh
            time_minutes: Total connection time in minutes
            idle_minutes: Idle time after charging complete (minutes)
            parking_minutes: Parking time in minutes

        Returns:
            Dictionary with cost breakdown by component
        """
        return {
            "flat_fee": self.flat_fee,
            "energy_cost": energy_kwh * self.energy_rate,
            "time_cost": time_minutes * self.time_rate,
            "idle_cost": idle_minutes * self.idle_rate,
            "parking_cost": parking_minutes * self.parking_rate,
            "total": self.calculate_cost(
                energy_kwh, time_minutes, idle_minutes, parking_minutes
            ),
        }

    @classmethod
    def from_mobie_data(cls, mobie_row: Dict) -> "Tariff":
        """
        Create Tariff from Mobie CSV data.

        Args:
            mobie_row: Dictionary containing Mobie tariff data

        Returns:
            Tariff instance

        Note:
            This is a placeholder implementation. Actual parsing logic will
            depend on the exact format of Mobie data fields like TIPO_TARIFA
            and TARIFA columns.
        """
        # Extract basic information
        tariff_id = mobie_row.get("UID_TOMADA", "")
        operator = mobie_row.get("OPERADOR", "")

        # Parse tariff type and rates
        # Format in Mobie data: "€ 0.261 /charge", "€ 0.1 /kWh", "€ 0.015 /minute"
        # This is a simplified parser - needs refinement based on actual data format

        tipo_tarifa = mobie_row.get("TIPO_TARIFA", "")
        tarifa = mobie_row.get("TARIFA", "")

        flat_fee = 0.0
        energy_rate = 0.0
        time_rate = 0.0

        # Parse tariff based on type
        # This logic should be refined based on actual Mobie data structure
        if "charge" in tipo_tarifa.lower() or "conexão" in tipo_tarifa.lower():
            # Flat fee
            flat_fee = cls._parse_rate(tarifa)
        elif "kwh" in tipo_tarifa.lower():
            # Energy-based
            energy_rate = cls._parse_rate(tarifa)
        elif "minute" in tipo_tarifa.lower() or "minuto" in tipo_tarifa.lower():
            # Time-based
            time_rate = cls._parse_rate(tarifa)

        return cls(
            id=tariff_id,
            operator=operator,
            flat_fee=flat_fee,
            energy_rate=energy_rate,
            time_rate=time_rate,
            currency="EUR",
        )

    @staticmethod
    def _parse_rate(tarifa_string: str) -> float:
        """
        Parse rate from Mobie tariff string.

        Args:
            tarifa_string: String like "€ 0.261 /charge" or "€ 0.1 /kWh"

        Returns:
            Parsed rate as float
        """
        import re

        # Extract numeric value from string
        match = re.search(r"[\d,\.]+", tarifa_string.replace("€", "").strip())
        if match:
            value_str = match.group().replace(",", ".")
            return float(value_str)
        return 0.0

    def __repr__(self) -> str:
        components = []
        if self.flat_fee > 0:
            components.append(f"flat={self.flat_fee}")
        if self.energy_rate > 0:
            components.append(f"energy={self.energy_rate}/kWh")
        if self.time_rate > 0:
            components.append(f"time={self.time_rate}/min")

        component_str = ", ".join(components) if components else "free"
        return f"Tariff(id='{self.id}', operator='{self.operator}', {component_str})"
