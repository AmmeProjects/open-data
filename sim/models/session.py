"""
Charging session models for input parameters and simulation results.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, TYPE_CHECKING
from datetime import datetime
import numpy as np

if TYPE_CHECKING:
    from sim.models.vehicle import Vehicle
    from sim.models.charger import Charger
    from sim.models.tariff import Tariff


@dataclass
class SessionParameters:
    """
    Input parameters for a charging session simulation.

    Attributes:
        vehicle: Vehicle model being charged
        charger: Charger being used
        start_soc: Starting state of charge (0-100%)
        target_soc: Target state of charge (0-100%)
        ambient_temp_c: Ambient temperature in Celsius (affects charging)
        battery_temp_c: Initial battery temperature in Celsius (if known)
        preconditioned: Whether battery was preconditioned for fast charging
        time_step_seconds: Simulation resolution in seconds (default: 60)
    """

    vehicle: "Vehicle"
    charger: "Charger"
    start_soc: float
    target_soc: float

    # Optional environmental parameters
    ambient_temp_c: Optional[float] = 25.0
    battery_temp_c: Optional[float] = None
    preconditioned: bool = False
    time_step_seconds: int = 60

    def __post_init__(self):
        """Validate session parameters."""
        if not 0 <= self.start_soc <= 100:
            raise ValueError(f"start_soc must be 0-100%, got {self.start_soc}")
        if not 0 <= self.target_soc <= 100:
            raise ValueError(f"target_soc must be 0-100%, got {self.target_soc}")
        if self.start_soc >= self.target_soc:
            raise ValueError(
                f"start_soc ({self.start_soc}%) must be less than target_soc ({self.target_soc}%)"
            )
        if self.time_step_seconds <= 0:
            raise ValueError(
                f"time_step_seconds must be positive, got {self.time_step_seconds}"
            )

    def __repr__(self) -> str:
        return (
            f"SessionParameters(vehicle='{self.vehicle.name}', "
            f"charger='{self.charger.name}', "
            f"soc={self.start_soc}%->{self.target_soc}%)"
        )


@dataclass
class SessionResult:
    """
    Output of a charging session simulation.

    Contains all results from the simulation including timing, energy, power profiles,
    and optional pricing information.

    Attributes:
        parameters: Input parameters used for simulation
        total_time_minutes: Total charging duration in minutes
        energy_added_kwh: Net energy added to battery (after losses)
        energy_delivered_kwh: Total energy delivered from grid (before losses)
        average_power_kw: Average charging power over the session
        peak_power_kw: Maximum power during the session
        time_series: Array of time points in minutes
        power_profile: Array of power values at each time point (kW)
        soc_profile: Array of SoC values at each time point (%)
        charging_efficiency: Overall efficiency (energy_added / energy_delivered)
        tariff: Optional tariff used for pricing
        total_cost: Total cost of the session (if tariff applied)
        cost_per_kwh: Cost per kWh added (if tariff applied)
        cost_breakdown: Detailed cost breakdown by component
        simulation_timestamp: When the simulation was run
    """

    # Input reference
    parameters: SessionParameters

    # Core results
    total_time_minutes: float
    energy_added_kwh: float
    energy_delivered_kwh: float
    average_power_kw: float
    peak_power_kw: float

    # Detailed profiles (repr=False to avoid cluttering print output)
    time_series: np.ndarray = field(repr=False)
    power_profile: np.ndarray = field(repr=False)
    soc_profile: np.ndarray = field(repr=False)

    # Efficiency
    charging_efficiency: float = 0.0

    # Pricing (optional)
    tariff: Optional["Tariff"] = None
    total_cost: Optional[float] = None
    cost_per_kwh: Optional[float] = None
    cost_breakdown: Optional[Dict[str, float]] = None

    # Metadata
    simulation_timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Calculate derived metrics."""
        if self.energy_delivered_kwh > 0:
            self.charging_efficiency = self.energy_added_kwh / self.energy_delivered_kwh

    def apply_tariff(
        self, tariff: "Tariff", idle_minutes: float = 0, parking_minutes: float = 0
    ) -> "SessionResult":
        """
        Apply tariff to calculate session costs.

        Args:
            tariff: Tariff model to apply
            idle_minutes: Additional idle time after charging (minutes)
            parking_minutes: Additional parking time (minutes)

        Returns:
            Self (for method chaining)
        """
        self.tariff = tariff

        # Calculate total cost
        self.total_cost = tariff.calculate_cost(
            energy_kwh=self.energy_delivered_kwh,
            time_minutes=self.total_time_minutes,
            idle_minutes=idle_minutes,
            parking_minutes=parking_minutes,
        )

        # Calculate cost per kWh added
        if self.energy_added_kwh > 0:
            self.cost_per_kwh = self.total_cost / self.energy_added_kwh
        else:
            self.cost_per_kwh = 0.0

        # Get detailed breakdown
        self.cost_breakdown = tariff.get_breakdown(
            energy_kwh=self.energy_delivered_kwh,
            time_minutes=self.total_time_minutes,
            idle_minutes=idle_minutes,
            parking_minutes=parking_minutes,
        )

        return self

    def summary(self) -> str:
        """
        Generate human-readable summary of the session.

        Returns:
            Formatted summary string
        """
        summary = f"""
Charging Session Summary
{"=" * 50}
Vehicle:         {self.parameters.vehicle.name}
Charger:         {self.parameters.charger.name}
SoC Range:       {self.parameters.start_soc:.0f}% → {self.parameters.target_soc:.0f}%

Results:
{"-" * 50}
Duration:        {self.total_time_minutes:.1f} minutes ({self.total_time_minutes / 60:.2f} hours)
Energy Added:    {self.energy_added_kwh:.2f} kWh (to battery)
Energy from Grid: {self.energy_delivered_kwh:.2f} kWh
Average Power:   {self.average_power_kw:.1f} kW
Peak Power:      {self.peak_power_kw:.1f} kW
Efficiency:      {self.charging_efficiency * 100:.1f}%
"""

        # Add pricing section if tariff was applied
        if self.total_cost is not None and self.tariff is not None:
            summary += f"""
Pricing:
{"-" * 50}
Operator:        {self.tariff.operator}
Total Cost:      {self.tariff.currency} {self.total_cost:.2f}
Cost per kWh:    {self.tariff.currency} {self.cost_per_kwh:.3f}/kWh

Breakdown:
  Flat fee:      {self.tariff.currency} {self.cost_breakdown["flat_fee"]:.2f}
  Energy cost:   {self.tariff.currency} {self.cost_breakdown["energy_cost"]:.2f} ({self.energy_delivered_kwh:.2f} kWh × {self.tariff.energy_rate:.3f})
  Time cost:     {self.tariff.currency} {self.cost_breakdown["time_cost"]:.2f} ({self.total_time_minutes:.1f} min × {self.tariff.time_rate:.4f})
"""
            if self.cost_breakdown.get("idle_cost", 0) > 0:
                summary += f"  Idle cost:     {self.tariff.currency} {self.cost_breakdown['idle_cost']:.2f}\n"
            if self.cost_breakdown.get("parking_cost", 0) > 0:
                summary += f"  Parking cost:  {self.tariff.currency} {self.cost_breakdown['parking_cost']:.2f}\n"

        return summary.strip()

    def plot(self):
        """
        Generate visualization of power and SoC profiles.

        Returns:
            matplotlib Figure object

        Raises:
            ImportError: If matplotlib is not installed
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            raise ImportError(
                "matplotlib is required for plotting. Install with: pip install matplotlib"
            )

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

        # Power profile
        ax1.plot(
            self.time_series,
            self.power_profile,
            "b-",
            linewidth=2,
            label="Charging Power",
        )
        ax1.axhline(
            self.average_power_kw,
            color="r",
            linestyle="--",
            alpha=0.7,
            label=f"Average: {self.average_power_kw:.1f} kW",
        )
        ax1.axhline(
            self.peak_power_kw,
            color="g",
            linestyle=":",
            alpha=0.7,
            label=f"Peak: {self.peak_power_kw:.1f} kW",
        )
        ax1.set_ylabel("Power (kW)", fontsize=11)
        ax1.set_title(
            f"Charging Session: {self.parameters.vehicle.name} @ {self.parameters.charger.name}",
            fontsize=12,
            fontweight="bold",
        )
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc="upper right")

        # SoC profile
        ax2.plot(self.time_series, self.soc_profile, "g-", linewidth=2)
        ax2.axhline(self.parameters.start_soc, color="r", linestyle="--", alpha=0.5)
        ax2.axhline(self.parameters.target_soc, color="r", linestyle="--", alpha=0.5)
        ax2.set_xlabel("Time (minutes)", fontsize=11)
        ax2.set_ylabel("State of Charge (%)", fontsize=11)
        ax2.set_ylim(0, 105)
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig

    def __repr__(self) -> str:
        return (
            f"SessionResult(time={self.total_time_minutes:.1f}min, "
            f"energy={self.energy_added_kwh:.2f}kWh, "
            f"avg_power={self.average_power_kw:.1f}kW)"
        )
