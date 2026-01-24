"""
Preset vehicle configurations for common electric vehicles.

This module contains predefined specifications for popular EV models,
making it easy to run simulations without manually defining vehicle parameters.
"""

from sim.models.vehicle import Vehicle, ChargingCurve


# ==============================================================================
# TESLA VEHICLES
# ==============================================================================

TESLA_MODEL_3_SR = Vehicle(
    name="Tesla Model 3 Standard Range",
    battery_capacity_kwh=60.0,
    nominal_voltage=360.0,
    max_ac_power_kw=11.0,
    max_dc_power_kw=170.0,
    max_current=472.0,
    charging_curve=ChargingCurve.piecewise(
        max_power_kw=170.0,
        constant_until=55.0,
        taper_start=80.0,
        taper_end_power_ratio=0.25,
    ),
    charging_efficiency=0.92,
)

TESLA_MODEL_3_LR = Vehicle(
    name="Tesla Model 3 Long Range",
    battery_capacity_kwh=82.0,
    nominal_voltage=360.0,
    max_ac_power_kw=11.0,
    max_dc_power_kw=250.0,
    max_current=694.0,
    charging_curve=ChargingCurve.piecewise(
        max_power_kw=250.0,
        constant_until=50.0,
        taper_start=75.0,
        taper_end_power_ratio=0.2,
    ),
    charging_efficiency=0.93,
)

TESLA_MODEL_Y_LR = Vehicle(
    name="Tesla Model Y Long Range",
    battery_capacity_kwh=81.0,
    nominal_voltage=360.0,
    max_ac_power_kw=11.0,
    max_dc_power_kw=250.0,
    max_current=694.0,
    charging_curve=ChargingCurve.piecewise(
        max_power_kw=250.0,
        constant_until=50.0,
        taper_start=75.0,
        taper_end_power_ratio=0.2,
    ),
    charging_efficiency=0.92,
)

# ==============================================================================
# VOLKSWAGEN ID SERIES
# ==============================================================================

VW_ID3_58KWH = Vehicle(
    name="Volkswagen ID.3 58kWh",
    battery_capacity_kwh=58.0,
    nominal_voltage=352.0,
    max_ac_power_kw=11.0,
    max_dc_power_kw=120.0,
    max_current=341.0,
    charging_curve=ChargingCurve.piecewise(
        max_power_kw=120.0,
        constant_until=38.0,
        taper_start=80.0,
        taper_end_power_ratio=0.25,
    ),
    charging_efficiency=0.90,
)

VW_ID3_77KWH = Vehicle(
    name="Volkswagen ID.3 77kWh",
    battery_capacity_kwh=77.0,
    nominal_voltage=352.0,
    max_ac_power_kw=11.0,
    max_dc_power_kw=170.0,
    max_current=483.0,
    charging_curve=ChargingCurve.piecewise(
        max_power_kw=170.0,
        constant_until=38.0,
        taper_start=82.0,
        taper_end_power_ratio=0.22,
    ),
    charging_efficiency=0.91,
)

VW_ID4_77KWH = Vehicle(
    name="Volkswagen ID.4 77kWh",
    battery_capacity_kwh=77.0,
    nominal_voltage=352.0,
    max_ac_power_kw=11.0,
    max_dc_power_kw=135.0,
    max_current=384.0,
    charging_curve=ChargingCurve.piecewise(
        max_power_kw=135.0,
        constant_until=40.0,
        taper_start=80.0,
        taper_end_power_ratio=0.23,
    ),
    charging_efficiency=0.90,
)

# ==============================================================================
# HYUNDAI/KIA E-GMP PLATFORM (800V)
# ==============================================================================

HYUNDAI_IONIQ5_77KWH = Vehicle(
    name="Hyundai Ioniq 5 77kWh",
    battery_capacity_kwh=77.4,
    nominal_voltage=697.0,  # 800V architecture
    max_ac_power_kw=11.0,
    max_dc_power_kw=235.0,
    max_current=337.0,
    charging_curve=ChargingCurve.piecewise(
        max_power_kw=235.0,
        constant_until=50.0,
        taper_start=80.0,
        taper_end_power_ratio=0.18,
    ),
    charging_efficiency=0.94,  # High efficiency due to 800V
)

KIA_EV6_77KWH = Vehicle(
    name="Kia EV6 77kWh",
    battery_capacity_kwh=77.4,
    nominal_voltage=697.0,  # 800V architecture
    max_ac_power_kw=11.0,
    max_dc_power_kw=240.0,
    max_current=344.0,
    charging_curve=ChargingCurve.piecewise(
        max_power_kw=240.0,
        constant_until=52.0,
        taper_start=80.0,
        taper_end_power_ratio=0.18,
    ),
    charging_efficiency=0.94,
)

# ==============================================================================
# RENAULT ZOE (Popular in Europe)
# ==============================================================================

RENAULT_ZOE_52KWH = Vehicle(
    name="Renault Zoe ZE50",
    battery_capacity_kwh=52.0,
    nominal_voltage=400.0,
    max_ac_power_kw=22.0,  # Notable for high AC charging power
    max_dc_power_kw=50.0,  # Limited DC charging
    max_current=125.0,
    charging_curve=ChargingCurve.constant_power(
        max_power_kw=50.0, taper_start_soc=85.0
    ),
    charging_efficiency=0.88,
)

# ==============================================================================
# NISSAN LEAF (CHAdeMO)
# ==============================================================================

NISSAN_LEAF_62KWH = Vehicle(
    name="Nissan Leaf e+ 62kWh",
    battery_capacity_kwh=62.0,
    nominal_voltage=360.0,
    max_ac_power_kw=6.6,
    max_dc_power_kw=100.0,  # CHAdeMO limited
    max_current=278.0,
    charging_curve=ChargingCurve.piecewise(
        max_power_kw=100.0,
        constant_until=60.0,
        taper_start=80.0,
        taper_end_power_ratio=0.20,
    ),
    charging_efficiency=0.89,
)

# ==============================================================================
# PORSCHE TAYCAN (High-performance 800V)
# ==============================================================================

PORSCHE_TAYCAN_93KWH = Vehicle(
    name="Porsche Taycan 4S 93kWh",
    battery_capacity_kwh=93.4,
    nominal_voltage=725.0,  # 800V architecture
    max_ac_power_kw=11.0,
    max_dc_power_kw=270.0,
    max_current=372.0,
    charging_curve=ChargingCurve.piecewise(
        max_power_kw=270.0,
        constant_until=35.0,
        taper_start=80.0,
        taper_end_power_ratio=0.15,
    ),
    charging_efficiency=0.95,
)

# ==============================================================================
# BMW iX (Latest generation)
# ==============================================================================

BMW_IX_111KWH = Vehicle(
    name="BMW iX xDrive50 111kWh",
    battery_capacity_kwh=111.5,
    nominal_voltage=396.0,
    max_ac_power_kw=11.0,
    max_dc_power_kw=195.0,
    max_current=492.0,
    charging_curve=ChargingCurve.piecewise(
        max_power_kw=195.0,
        constant_until=50.0,
        taper_start=80.0,
        taper_end_power_ratio=0.20,
    ),
    charging_efficiency=0.91,
)

# ==============================================================================
# PEUGEOT e-208 (Compact EV)
# ==============================================================================

PEUGEOT_E208_50KWH = Vehicle(
    name="Peugeot e-208 50kWh",
    battery_capacity_kwh=50.0,
    nominal_voltage=330.0,
    max_ac_power_kw=11.0,
    max_dc_power_kw=100.0,
    max_current=303.0,
    charging_curve=ChargingCurve.constant_power(
        max_power_kw=100.0, taper_start_soc=80.0
    ),
    charging_efficiency=0.89,
)

# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [
    # Tesla
    "TESLA_MODEL_3_SR",
    "TESLA_MODEL_3_LR",
    "TESLA_MODEL_Y_LR",
    # Volkswagen ID
    "VW_ID3_58KWH",
    "VW_ID3_77KWH",
    "VW_ID4_77KWH",
    # Hyundai/Kia E-GMP
    "HYUNDAI_IONIQ5_77KWH",
    "KIA_EV6_77KWH",
    # Renault
    "RENAULT_ZOE_52KWH",
    # Nissan
    "NISSAN_LEAF_62KWH",
    # Porsche
    "PORSCHE_TAYCAN_93KWH",
    # BMW
    "BMW_IX_111KWH",
    # Peugeot
    "PEUGEOT_E208_50KWH",
]
