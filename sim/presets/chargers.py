"""
Preset charger configurations for common charging networks and types.

This module contains predefined specifications for various charger types,
from slow AC chargers to ultra-fast DC chargers.
"""

from sim.models.charger import Charger, ChargerType


# ==============================================================================
# AC CHARGERS (Type 2 / Mennekes)
# ==============================================================================

AC_TYPE2_3_7KW = Charger(
    name="Type 2 3.7kW (1-phase)",
    charger_type=ChargerType.AC,
    connector_type="Type2",
    max_voltage=230.0,
    max_current=16.0,
    max_power_kw=3.7,
    phases=1,
)

AC_TYPE2_7_4KW = Charger(
    name="Type 2 7.4kW (1-phase)",
    charger_type=ChargerType.AC,
    connector_type="Type2",
    max_voltage=230.0,
    max_current=32.0,
    max_power_kw=7.4,
    phases=1,
)

AC_TYPE2_11KW = Charger(
    name="Type 2 11kW (3-phase)",
    charger_type=ChargerType.AC,
    connector_type="Type2",
    max_voltage=400.0,
    max_current=16.0,
    max_power_kw=11.0,
    phases=3,
)

AC_TYPE2_22KW = Charger(
    name="Type 2 22kW (3-phase)",
    charger_type=ChargerType.AC,
    connector_type="Type2",
    max_voltage=400.0,
    max_current=32.0,
    max_power_kw=22.0,
    phases=3,
)

AC_TYPE2_43KW = Charger(
    name="Type 2 43kW (3-phase)",
    charger_type=ChargerType.AC,
    connector_type="Type2",
    max_voltage=400.0,
    max_current=63.0,
    max_power_kw=43.0,
    phases=3,
)

# ==============================================================================
# DC FAST CHARGERS - CCS (Combined Charging System)
# ==============================================================================

DC_CCS_50KW = Charger(
    name="CCS 50kW DC Fast Charger",
    charger_type=ChargerType.DC,
    connector_type="CCS",
    max_voltage=500.0,
    max_current=125.0,
    max_power_kw=50.0,
    phases=3,  # Not used for DC, but kept for consistency
)

DC_CCS_100KW = Charger(
    name="CCS 100kW DC Fast Charger",
    charger_type=ChargerType.DC,
    connector_type="CCS",
    max_voltage=500.0,
    max_current=200.0,
    max_power_kw=100.0,
    phases=3,
)

DC_CCS_150KW = Charger(
    name="CCS 150kW DC Fast Charger",
    charger_type=ChargerType.DC,
    connector_type="CCS",
    max_voltage=500.0,
    max_current=300.0,
    max_power_kw=150.0,
    phases=3,
)

DC_CCS_175KW = Charger(
    name="CCS 175kW DC Fast Charger",
    charger_type=ChargerType.DC,
    connector_type="CCS",
    max_voltage=500.0,
    max_current=350.0,
    max_power_kw=175.0,
    phases=3,
)

DC_CCS_350KW = Charger(
    name="CCS 350kW Ultra-Fast Charger",
    charger_type=ChargerType.DC,
    connector_type="CCS",
    max_voltage=920.0,  # Supports 800V vehicles
    max_current=500.0,
    max_power_kw=350.0,
    phases=3,
)

# ==============================================================================
# DC FAST CHARGERS - CHAdeMO (Nissan standard)
# ==============================================================================

DC_CHADEMO_50KW = Charger(
    name="CHAdeMO 50kW DC Fast Charger",
    charger_type=ChargerType.DC,
    connector_type="CHAdeMO",
    max_voltage=500.0,
    max_current=125.0,
    max_power_kw=50.0,
    phases=3,
)

DC_CHADEMO_62_5KW = Charger(
    name="CHAdeMO 62.5kW DC Fast Charger",
    charger_type=ChargerType.DC,
    connector_type="CHAdeMO",
    max_voltage=500.0,
    max_current=125.0,
    max_power_kw=62.5,
    phases=3,
)

DC_CHADEMO_100KW = Charger(
    name="CHAdeMO 100kW DC Fast Charger",
    charger_type=ChargerType.DC,
    connector_type="CHAdeMO",
    max_voltage=500.0,
    max_current=200.0,
    max_power_kw=100.0,
    phases=3,
)

# ==============================================================================
# SPECIFIC CHARGING NETWORKS
# ==============================================================================

# IONITY - European ultra-fast charging network
IONITY_350KW = Charger(
    name="IONITY 350kW",
    charger_type=ChargerType.DC,
    connector_type="CCS",
    max_voltage=920.0,
    max_current=500.0,
    max_power_kw=350.0,
    phases=3,
)

# Tesla Supercharger V2
TESLA_SUPERCHARGER_V2 = Charger(
    name="Tesla Supercharger V2",
    charger_type=ChargerType.DC,
    connector_type="CCS",  # In Europe, now uses CCS
    max_voltage=480.0,
    max_current=312.0,
    max_power_kw=150.0,
    phases=3,
)

# Tesla Supercharger V3
TESLA_SUPERCHARGER_V3 = Charger(
    name="Tesla Supercharger V3",
    charger_type=ChargerType.DC,
    connector_type="CCS",
    max_voltage=500.0,
    max_current=500.0,
    max_power_kw=250.0,
    phases=3,
)

# Tesla Supercharger V4
TESLA_SUPERCHARGER_V4 = Charger(
    name="Tesla Supercharger V4",
    charger_type=ChargerType.DC,
    connector_type="CCS",
    max_voltage=1000.0,  # Supports 800V vehicles
    max_current=615.0,
    max_power_kw=350.0,  # Currently limited to 250kW for Teslas
    phases=3,
)

# Fastned - Netherlands-based fast charging network
FASTNED_300KW = Charger(
    name="Fastned 300kW",
    charger_type=ChargerType.DC,
    connector_type="CCS",
    max_voltage=920.0,
    max_current=500.0,
    max_power_kw=300.0,
    phases=3,
)

# EDP (Portugal) - Common AC chargers
EDP_MOBIE_22KW = Charger(
    name="EDP Mobie 22kW",
    charger_type=ChargerType.AC,
    connector_type="Type2",
    max_voltage=400.0,
    max_current=32.0,
    max_power_kw=22.0,
    phases=3,
)

# EDP (Portugal) - DC fast chargers
EDP_MOBIE_50KW = Charger(
    name="EDP Mobie 50kW DC",
    charger_type=ChargerType.DC,
    connector_type="CCS",
    max_voltage=500.0,
    max_current=125.0,
    max_power_kw=50.0,
    phases=3,
)

# ==============================================================================
# HOME/WORKPLACE CHARGERS
# ==============================================================================

HOME_WALLBOX_7_4KW = Charger(
    name="Home Wallbox 7.4kW",
    charger_type=ChargerType.AC,
    connector_type="Type2",
    max_voltage=230.0,
    max_current=32.0,
    max_power_kw=7.4,
    phases=1,
)

HOME_WALLBOX_11KW = Charger(
    name="Home Wallbox 11kW",
    charger_type=ChargerType.AC,
    connector_type="Type2",
    max_voltage=400.0,
    max_current=16.0,
    max_power_kw=11.0,
    phases=3,
)

WORKPLACE_22KW = Charger(
    name="Workplace 22kW",
    charger_type=ChargerType.AC,
    connector_type="Type2",
    max_voltage=400.0,
    max_current=32.0,
    max_power_kw=22.0,
    phases=3,
)

# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [
    # AC Chargers
    "AC_TYPE2_3_7KW",
    "AC_TYPE2_7_4KW",
    "AC_TYPE2_11KW",
    "AC_TYPE2_22KW",
    "AC_TYPE2_43KW",
    # DC CCS Chargers
    "DC_CCS_50KW",
    "DC_CCS_100KW",
    "DC_CCS_150KW",
    "DC_CCS_175KW",
    "DC_CCS_350KW",
    # DC CHAdeMO Chargers
    "DC_CHADEMO_50KW",
    "DC_CHADEMO_62_5KW",
    "DC_CHADEMO_100KW",
    # Network Specific
    "IONITY_350KW",
    "TESLA_SUPERCHARGER_V2",
    "TESLA_SUPERCHARGER_V3",
    "TESLA_SUPERCHARGER_V4",
    "FASTNED_300KW",
    "EDP_MOBIE_22KW",
    "EDP_MOBIE_50KW",
    # Home/Workplace
    "HOME_WALLBOX_7_4KW",
    "HOME_WALLBOX_11KW",
    "WORKPLACE_22KW",
]
