"""
Charger models for EV charging simulation.
"""

from dataclasses import dataclass
from enum import Enum


class ChargerType(Enum):
    """Types of EV chargers."""

    AC = "AC"  # Alternating Current (slow/medium charging)
    DC = "DC"  # Direct Current (fast charging)


@dataclass
class Charger:
    """
    Electric vehicle charger specifications.

    Attributes:
        name: Charger model/network name (e.g., "IONITY 350kW", "Type 2 22kW")
        charger_type: ChargerType.AC or ChargerType.DC
        connector_type: Connector standard (e.g., "Type2", "CCS", "CHAdeMO")
        max_voltage: Maximum voltage in Volts
        max_current: Maximum current in Amperes
        max_power_kw: Maximum power output in kW
        phases: Number of phases for AC chargers (1 or 3), not applicable for DC
    """

    name: str
    charger_type: ChargerType
    connector_type: str
    max_voltage: float
    max_current: float
    max_power_kw: float
    phases: int = 3

    def __post_init__(self):
        """Validate charger parameters."""
        if self.max_voltage <= 0:
            raise ValueError(f"max_voltage must be positive, got {self.max_voltage}")
        if self.max_current <= 0:
            raise ValueError(f"max_current must be positive, got {self.max_current}")
        if self.max_power_kw <= 0:
            raise ValueError(f"max_power_kw must be positive, got {self.max_power_kw}")
        if self.phases not in (1, 3):
            raise ValueError(f"phases must be 1 or 3, got {self.phases}")
        if self.charger_type == ChargerType.AC and self.phases not in (1, 3):
            raise ValueError(f"AC charger must have 1 or 3 phases, got {self.phases}")

    def is_compatible(self, connector_type: str) -> bool:
        """
        Check if charger connector is compatible with vehicle connector.

        Args:
            connector_type: Vehicle's connector type

        Returns:
            True if compatible, False otherwise
        """
        # Simplified compatibility check
        # In reality, this would be more complex with adapter support
        return self.connector_type.lower() == connector_type.lower()

    def __repr__(self) -> str:
        return (
            f"Charger(name='{self.name}', "
            f"type={self.charger_type.value}, "
            f"max_power={self.max_power_kw}kW)"
        )
