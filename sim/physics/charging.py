"""
Physics engine for EV charging calculations.

This module implements the core charging physics, including:
- AC charging calculations (3-phase and single-phase)
- DC charging with vehicle-specific charging curves
- Power limiting based on charger and vehicle constraints
- Energy accumulation and SoC updates
"""

from typing import TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from sim.models.session import SessionParameters, SessionResult
    from sim.models.vehicle import Vehicle
    from sim.models.charger import Charger
    from sim.models.tariff import Tariff

from sim.models.charger import ChargerType


def calculate_ac_power(
    voltage: float,
    current: float,
    phases: int = 3,
    power_factor: float = 0.99,
    efficiency: float = 0.90,
) -> float:
    """
    Calculate AC charging power.

    Args:
        voltage: Voltage in Volts
        current: Current in Amperes
        phases: Number of phases (1 or 3)
        power_factor: Power factor (typically 0.95-0.99)
        efficiency: Charging efficiency (typically 0.85-0.95)

    Returns:
        Power in kW (accounting for efficiency losses)
    """
    if phases == 3:
        # Three-phase: P = √3 × V × I × PF
        power_kw = (np.sqrt(3) * voltage * current * power_factor) / 1000.0
    else:
        # Single-phase: P = V × I × PF
        power_kw = (voltage * current * power_factor) / 1000.0

    return power_kw * efficiency


def determine_charging_power(
    charger: "Charger",
    vehicle: "Vehicle",
    soc_percent: float,
) -> float:
    """
    Determine actual charging power based on charger and vehicle limits.

    The actual power is the minimum of:
    - Charger maximum power
    - Vehicle maximum power (AC or DC)
    - Vehicle charging curve limit (for DC)

    Args:
        charger: Charger being used
        vehicle: Vehicle being charged
        soc_percent: Current state of charge (0-100%)

    Returns:
        Actual charging power in kW
    """
    is_dc = charger.charger_type == ChargerType.DC

    # Get vehicle's max power at current SoC
    vehicle_max_power = vehicle.get_max_power_at_soc(soc_percent, is_dc=is_dc)

    # Actual power is limited by both charger and vehicle
    if is_dc:
        # DC charging: direct power delivery
        actual_power = min(charger.max_power_kw, vehicle_max_power)
    else:
        # AC charging: calculate from electrical parameters
        ac_power = calculate_ac_power(
            voltage=charger.max_voltage,
            current=charger.max_current,
            phases=charger.phases,
            power_factor=0.99,
            efficiency=vehicle.charging_efficiency,
        )
        actual_power = min(ac_power, vehicle_max_power)

    return actual_power


def calculate_charging_session(parameters: "SessionParameters") -> "SessionResult":
    """
    Simulate a complete charging session with minute-by-minute resolution.

    This is the main physics engine that simulates the charging process from
    start_soc to target_soc, accounting for:
    - Charger and vehicle power limits
    - Vehicle charging curves (for DC)
    - Charging efficiency
    - Time-varying power delivery

    Args:
        parameters: SessionParameters with all input configuration

    Returns:
        SessionResult with complete simulation output including:
        - Total charging time (minutes)
        - Energy added (kWh) and delivered (kWh)
        - Average/peak power (kW)
        - Power, SoC, and time profiles
        - Efficiency metrics

    Raises:
        ValueError: If parameters are invalid
    """
    from sim.models.session import SessionResult

    vehicle = parameters.vehicle
    charger = parameters.charger
    time_step_hours = parameters.time_step_seconds / 3600.0

    # Initialize state
    current_soc = parameters.start_soc
    target_soc = parameters.target_soc

    # Storage for time series data
    time_points = [0.0]  # minutes
    power_points = []
    soc_points = [current_soc]

    # Energy tracking
    total_energy_delivered = 0.0  # From grid (before losses)
    total_energy_added = 0.0  # To battery (after losses)

    current_time = 0.0  # minutes

    # Simulation loop
    while current_soc < target_soc:
        # Determine charging power at current SoC
        power_kw = determine_charging_power(charger, vehicle, current_soc)

        # If power drops to very low levels, we're essentially done
        if power_kw < 0.1:
            break

        # Calculate energy delivered in this time step
        energy_step_kwh = power_kw * time_step_hours

        # Account for vehicle charging efficiency
        # (energy actually added to battery vs. energy from grid)
        energy_added_step = energy_step_kwh * vehicle.charging_efficiency

        # Update battery SoC
        soc_increase = (energy_added_step / vehicle.battery_capacity_kwh) * 100.0
        current_soc += soc_increase

        # Don't overshoot target
        if current_soc > target_soc:
            # Adjust the last step proportionally
            overshoot_ratio = (current_soc - target_soc) / soc_increase
            energy_step_kwh *= 1.0 - overshoot_ratio
            energy_added_step *= 1.0 - overshoot_ratio
            current_soc = target_soc

        # Update energy totals
        total_energy_delivered += energy_step_kwh
        total_energy_added += energy_added_step

        # Record data points
        power_points.append(power_kw)
        current_time += parameters.time_step_seconds / 60.0
        time_points.append(current_time)
        soc_points.append(current_soc)

        # Safety check to prevent infinite loops
        if current_time > 24 * 60:  # 24 hours
            raise RuntimeError(
                f"Simulation exceeded 24 hours. Check parameters: "
                f"SoC only reached {current_soc:.1f}% (target: {target_soc:.1f}%)"
            )

    # Calculate summary statistics
    power_array = np.array(power_points)
    average_power = (
        total_energy_delivered / (current_time / 60.0) if current_time > 0 else 0.0
    )
    peak_power = float(np.max(power_array)) if len(power_array) > 0 else 0.0

    # Create result object
    result = SessionResult(
        parameters=parameters,
        total_time_minutes=current_time,
        energy_added_kwh=total_energy_added,
        energy_delivered_kwh=total_energy_delivered,
        average_power_kw=average_power,
        peak_power_kw=peak_power,
        time_series=np.array(time_points[:-1]),  # Exclude last point (redundant)
        power_profile=power_array,
        soc_profile=np.array(soc_points[:-1]),  # Match power profile length
    )

    return result


def simulate_session(
    charger: "Charger",
    vehicle: "Vehicle",
    start_soc: float,
    target_soc: float,
    tariff: "Tariff" = None,
    **kwargs,
) -> "SessionResult":
    """
    Convenience wrapper for quick charging session simulations.

    This is a simplified interface to calculate_charging_session that
    handles creating SessionParameters automatically.

    Args:
        charger: Charger being used
        vehicle: Vehicle being charged
        start_soc: Starting state of charge (0-100%)
        target_soc: Target state of charge (0-100%)
        tariff: Optional tariff for cost calculation
        **kwargs: Additional parameters passed to SessionParameters
                 (ambient_temp_c, battery_temp_c, preconditioned, time_step_seconds)

    Returns:
        SessionResult with simulation output and pricing (if tariff provided)

    Example:
        >>> from sim.presets import vehicles, chargers
        >>> result = simulate_session(
        ...     charger=chargers.IONITY_350KW,
        ...     vehicle=vehicles.TESLA_MODEL_3_LR,
        ...     start_soc=20,
        ...     target_soc=80
        ... )
        >>> print(f"Charging time: {result.total_time_minutes:.1f} minutes")
        >>> print(f"Energy added: {result.energy_added_kwh:.2f} kWh")
    """
    from sim.models.session import SessionParameters

    # Create parameters
    params = SessionParameters(
        vehicle=vehicle,
        charger=charger,
        start_soc=start_soc,
        target_soc=target_soc,
        **kwargs,
    )

    # Run simulation
    result = calculate_charging_session(params)

    # Apply tariff if provided
    if tariff is not None:
        result.apply_tariff(tariff)

    return result


def estimate_charging_time(
    charger: "Charger",
    vehicle: "Vehicle",
    start_soc: float,
    target_soc: float,
) -> float:
    """
    Quick estimation of charging time without full simulation.

    This provides a rough estimate based on average power, useful for
    quick calculations when full simulation detail is not needed.

    Args:
        charger: Charger being used
        vehicle: Vehicle being charged
        start_soc: Starting state of charge (0-100%)
        target_soc: Target state of charge (0-100%)

    Returns:
        Estimated charging time in minutes

    Note:
        This is an approximation. For accurate results, use simulate_session()
        or calculate_charging_session().
    """
    # Calculate energy needed
    soc_delta = target_soc - start_soc
    energy_needed = (soc_delta / 100.0) * vehicle.battery_capacity_kwh

    # Estimate average power (use midpoint SoC)
    mid_soc = (start_soc + target_soc) / 2.0
    avg_power = determine_charging_power(charger, vehicle, mid_soc)

    # Account for efficiency
    energy_from_grid = energy_needed / vehicle.charging_efficiency

    # Calculate time
    if avg_power > 0:
        time_hours = energy_from_grid / avg_power
        return time_hours * 60.0
    else:
        return float("inf")


__all__ = [
    "calculate_ac_power",
    "determine_charging_power",
    "calculate_charging_session",
    "simulate_session",
    "estimate_charging_time",
]
