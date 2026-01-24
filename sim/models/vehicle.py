"""
Vehicle and charging curve models for EV charging simulation.
"""

from dataclasses import dataclass
from typing import Optional, List, Tuple
import numpy as np


class ChargingCurve:
    """
    Represents DC fast charging power curve as a function of State of Charge (SoC).

    The charging curve defines the maximum power the vehicle can accept at different
    battery charge levels. Typically, DC fast charging maintains constant power
    until ~80% SoC, then tapers off to protect the battery.
    """

    def __init__(self, curve_points: List[Tuple[float, float]]):
        """
        Initialize charging curve from list of (SoC%, power_kW) points.

        Args:
            curve_points: List of tuples (soc_percent, power_kw) defining the curve.
                         Points will be sorted by SoC and interpolated linearly.
                         Example: [(0, 150), (50, 150), (80, 75), (100, 25)]

        Raises:
            ValueError: If curve_points is empty or contains invalid values.
        """
        if not curve_points:
            raise ValueError("curve_points cannot be empty")

        # Sort by SoC and validate
        sorted_points = sorted(curve_points, key=lambda x: x[0])
        for soc, power in sorted_points:
            if not 0 <= soc <= 100:
                raise ValueError(f"SoC must be between 0-100%, got {soc}")
            if power < 0:
                raise ValueError(f"Power must be non-negative, got {power}")

        self.soc_points = np.array([p[0] for p in sorted_points])
        self.power_points = np.array([p[1] for p in sorted_points])

    def get_max_power_at_soc(self, soc_percent: float) -> float:
        """
        Get maximum charging power at given State of Charge.

        Args:
            soc_percent: State of charge in percent (0-100)

        Returns:
            Maximum charging power in kW at the given SoC

        Raises:
            ValueError: If soc_percent is outside valid range
        """
        if not 0 <= soc_percent <= 100:
            raise ValueError(f"SoC must be between 0-100%, got {soc_percent}")

        # Linear interpolation
        return float(np.interp(soc_percent, self.soc_points, self.power_points))

    @classmethod
    def constant_power(
        cls, max_power_kw: float, taper_start_soc: float = 80.0
    ) -> "ChargingCurve":
        """
        Create a simple constant power curve with linear taper.

        Args:
            max_power_kw: Maximum charging power in kW
            taper_start_soc: SoC percentage where tapering begins (default 80%)

        Returns:
            ChargingCurve with constant power until taper_start_soc, then linear taper to 20% at 100%
        """
        return cls(
            [
                (0, max_power_kw),
                (taper_start_soc, max_power_kw),
                (100, max_power_kw * 0.2),  # Taper to 20% at full
            ]
        )

    @classmethod
    def piecewise(
        cls,
        max_power_kw: float,
        constant_until: float = 50.0,
        taper_start: float = 80.0,
        taper_end_power_ratio: float = 0.2,
    ) -> "ChargingCurve":
        """
        Create a realistic piecewise charging curve.

        Args:
            max_power_kw: Maximum charging power in kW
            constant_until: SoC where constant power phase ends
            taper_start: SoC where significant tapering begins
            taper_end_power_ratio: Power ratio at 100% SoC (default 0.2 = 20%)

        Returns:
            ChargingCurve with realistic charging profile
        """
        return cls(
            [
                (0, max_power_kw),
                (constant_until, max_power_kw),
                (taper_start, max_power_kw * 0.9),
                (90, max_power_kw * 0.5),
                (100, max_power_kw * taper_end_power_ratio),
            ]
        )

    def __repr__(self) -> str:
        return f"ChargingCurve(points={len(self.soc_points)})"


@dataclass
class Vehicle:
    """
    Electric vehicle specifications for charging simulation.

    Attributes:
        name: Vehicle model name (e.g., "Tesla Model 3 Long Range")
        battery_capacity_kwh: Total battery pack capacity in kWh
        nominal_voltage: Nominal battery pack voltage (e.g., 400V or 800V)
        max_ac_power_kw: Maximum AC charging power in kW (typically 7-22 kW)
        max_dc_power_kw: Maximum DC fast charging power in kW
        max_current: Maximum charging current in Amperes
        charging_curve: Optional ChargingCurve for DC fast charging behavior
        charging_efficiency: Charging efficiency (0-1), accounts for conversion losses
    """

    name: str
    battery_capacity_kwh: float
    nominal_voltage: float
    max_ac_power_kw: float
    max_dc_power_kw: float
    max_current: float
    charging_curve: Optional[ChargingCurve] = None
    charging_efficiency: float = 0.90

    def __post_init__(self):
        """Validate vehicle parameters."""
        if self.battery_capacity_kwh <= 0:
            raise ValueError(
                f"battery_capacity_kwh must be positive, got {self.battery_capacity_kwh}"
            )
        if self.nominal_voltage <= 0:
            raise ValueError(
                f"nominal_voltage must be positive, got {self.nominal_voltage}"
            )
        if self.max_ac_power_kw <= 0:
            raise ValueError(
                f"max_ac_power_kw must be positive, got {self.max_ac_power_kw}"
            )
        if self.max_dc_power_kw <= 0:
            raise ValueError(
                f"max_dc_power_kw must be positive, got {self.max_dc_power_kw}"
            )
        if self.max_current <= 0:
            raise ValueError(f"max_current must be positive, got {self.max_current}")
        if not 0 < self.charging_efficiency <= 1:
            raise ValueError(
                f"charging_efficiency must be between 0 and 1, got {self.charging_efficiency}"
            )

        # Create default charging curve if not provided
        if self.charging_curve is None:
            self.charging_curve = ChargingCurve.constant_power(self.max_dc_power_kw)

    def get_max_power_at_soc(self, soc_percent: float, is_dc: bool = True) -> float:
        """
        Get maximum charging power at given SoC.

        Args:
            soc_percent: State of charge in percent (0-100)
            is_dc: Whether DC charging (uses curve) or AC (constant)

        Returns:
            Maximum power in kW
        """
        if is_dc and self.charging_curve:
            return min(
                self.max_dc_power_kw,
                self.charging_curve.get_max_power_at_soc(soc_percent),
            )
        elif is_dc:
            return self.max_dc_power_kw
        else:
            return self.max_ac_power_kw

    def __repr__(self) -> str:
        return (
            f"Vehicle(name='{self.name}', "
            f"battery={self.battery_capacity_kwh}kWh, "
            f"max_dc={self.max_dc_power_kw}kW)"
        )
