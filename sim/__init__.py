"""
EV Charging Simulation Module

This module provides tools for simulating electric vehicle charging sessions,
including physics-based calculations, tariff pricing, and statistical analysis.
"""

__version__ = "0.1.0"

from sim.models import (
    Vehicle,
    Charger,
    ChargingCurve,
    Tariff,
    SessionParameters,
    SessionResult,
    ChargerType,
    TariffType,
)

from sim.physics import (
    simulate_session,
    calculate_charging_session,
    estimate_charging_time,
)

__all__ = [
    # Models
    "Vehicle",
    "Charger",
    "ChargingCurve",
    "Tariff",
    "SessionParameters",
    "SessionResult",
    "ChargerType",
    "TariffType",
    # Physics
    "simulate_session",
    "calculate_charging_session",
    "estimate_charging_time",
]
