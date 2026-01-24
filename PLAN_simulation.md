## Plan for EV Charging Simulation Module

Based on your project structure and goals, here's a structured plan:

### **1. Architecture Overview**

I recommend creating a new `sim/` package at the root level (parallel to src) to keep simulation logic separate from data collection:

```
open-data/
├── src/          # Data collection & processing
├── sim/          # Simulation & modeling (NEW)
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── charger.py      # Charger specifications
│   │   ├── vehicle.py      # Vehicle specifications & charging curves
│   │   ├── tariff.py       # Tariff/pricing models
│   │   └── session.py      # Charging session model (input & output)
│   ├── physics/
│   │   ├── __init__.py
│   │   └── charging.py     # Charging physics & calculations
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── pricing.py      # Cost analysis integration
│   │   └── statistics.py   # Statistical analysis of sessions
│   └── presets/
│       ├── __init__.py
│       ├── chargers.py     # Common charger specifications
│       └── vehicles.py     # Common vehicle profiles
└── notebooks/
    └── charging_simulation.ipynb  (NEW)
```

### **2. Core Components**

#### **A. Vehicle Model** (`sim/models/vehicle.py`)
```python
@dataclass
class Vehicle:
    name: str
    battery_capacity_kwh: float          # Pack capacity (e.g., 75 kWh)
    nominal_voltage: float               # Nominal pack voltage (e.g., 400V)
    max_ac_power_kw: float              # Max AC charging power
    max_dc_power_kw: float              # Max DC charging power
    max_current: float                  # Max current
    charging_curve: Optional[ChargingCurve] = None  # For DC fast charging
    charging_efficiency: float = 0.90    # Typical 85-95%
```

#### **B. Charger Model** (`sim/models/charger.py`)
```python
@dataclass
class Charger:
    name: str
    charger_type: ChargerType  # AC / DC
    connector_type: str         # Type2, CCS, CHAdeMO, etc.
    max_voltage: float
    max_current: float
    max_power_kw: float
    phases: int = 3            # For AC chargers
```

#### **C. Charging Curve** (`sim/models/vehicle.py`)
- **Option 1**: Simple linear approximation
  - Constant power until ~80% SoC, then taper
- **Option 2**: Piecewise function based on SoC ranges
- **Option 3**: Real curve data (when available)

```python
class ChargingCurve:
    """Represents DC fast charging power curve vs SoC"""
    def get_max_power_at_soc(self, soc_percent: float) -> float:
        """Returns max power in kW at given SoC percentage"""
```

#### **D. Tariff Model** (`sim/models/tariff.py`)
```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict

class TariffType(Enum):
    """Types of charging tariff components"""
    FLAT = "flat"           # Fixed fee per session
    ENERGY = "energy"       # Per kWh consumed
    TIME = "time"           # Per minute connected
    IDLE = "idle"           # Per minute after charging complete
    PARKING = "parking"     # Parking fee

@dataclass
class TariffComponent:
    """Individual tariff component"""
    type: TariffType
    rate: float             # Amount in currency (e.g., EUR)
    unit: str               # 'session', 'kWh', 'minute', etc.
    
    def calculate(self, value: float) -> float:
        """Calculate cost for given usage value"""
        return self.rate * value

@dataclass
class Tariff:
    """Complete tariff structure for a charging location"""
    id: str
    operator: str
    location_id: Optional[str] = None
    connector_id: Optional[str] = None
    
    # Tariff components
    flat_fee: float = 0.0           # EUR per session
    energy_rate: float = 0.0        # EUR per kWh
    time_rate: float = 0.0          # EUR per minute
    idle_rate: float = 0.0          # EUR per minute (after charging)
    parking_rate: float = 0.0       # EUR per minute
    
    # Time-of-use (optional for future)
    time_of_use: Optional[Dict[str, 'Tariff']] = None  # e.g., {'peak': Tariff(...), 'off_peak': Tariff(...)}
    
    # Metadata
    currency: str = "EUR"
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None
    
    def calculate_cost(self, energy_kwh: float, time_minutes: float, 
                      idle_minutes: float = 0, parking_minutes: float = 0) -> float:
        """Calculate total cost for a charging session"""
        cost = (
            self.flat_fee +
            (energy_kwh * self.energy_rate) +
            (time_minutes * self.time_rate) +
            (idle_minutes * self.idle_rate) +
            (parking_minutes * self.parking_rate)
        )
        return cost
    
    @classmethod
    def from_mobie_data(cls, mobie_row: Dict) -> 'Tariff':
        """Create Tariff from Mobie CSV data"""
        # Parse rates from Mobie format: "€ 0.261 /charge", "€ 0.1 /kWh", etc.
        return cls(
            id=mobie_row['UID_TOMADA'],
            operator=mobie_row['OPERADOR'],
            # ... parse rates from TIPO_TARIFA and TARIFA columns
        )
```

#### **E. Session Model** (`sim/models/session.py`)
```python
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
import numpy as np

@dataclass
class SessionParameters:
    """Input parameters for a charging session simulation"""
    vehicle: 'Vehicle'
    charger: 'Charger'
    start_soc: float        # Starting state of charge (0-100%)
    target_soc: float       # Target state of charge (0-100%)
    
    # Optional parameters
    ambient_temp_c: Optional[float] = 25.0
    battery_temp_c: Optional[float] = None  # If None, assume optimal
    preconditioned: bool = False
    time_step_seconds: int = 60  # Simulation resolution
    
    def __post_init__(self):
        """Validate parameters"""
        if not 0 <= self.start_soc <= 100:
            raise ValueError(f"start_soc must be 0-100, got {self.start_soc}")
        if not 0 <= self.target_soc <= 100:
            raise ValueError(f"target_soc must be 0-100, got {self.target_soc}")
        if self.start_soc >= self.target_soc:
            raise ValueError(f"start_soc must be less than target_soc")

@dataclass
class SessionResult:
    """Output of a charging session simulation"""
    # Input reference
    parameters: SessionParameters
    
    # Core results
    total_time_minutes: float
    energy_added_kwh: float
    energy_delivered_kwh: float  # From grid (includes losses)
    average_power_kw: float
    peak_power_kw: float
    
    # Detailed profile
    time_series: np.ndarray = field(repr=False)  # Time points (minutes)
    power_profile: np.ndarray = field(repr=False)  # Power at each time point (kW)
    soc_profile: np.ndarray = field(repr=False)  # SoC at each time point (%)
    
    # Efficiency
    charging_efficiency: float = 0.0  # energy_added / energy_delivered
    
    # Pricing (populated separately)
    tariff: Optional['Tariff'] = None
    total_cost: Optional[float] = None
    cost_per_kwh: Optional[float] = None
    cost_breakdown: Optional[Dict[str, float]] = None
    
    # Metadata
    simulation_timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Calculate derived metrics"""
        if self.energy_added_kwh > 0:
            self.charging_efficiency = self.energy_added_kwh / self.energy_delivered_kwh
    
    def apply_tariff(self, tariff: 'Tariff') -> 'SessionResult':
        """Calculate costs based on tariff structure"""
        self.tariff = tariff
        self.total_cost = tariff.calculate_cost(
            energy_kwh=self.energy_delivered_kwh,
            time_minutes=self.total_time_minutes
        )
        
        if self.energy_added_kwh > 0:
            self.cost_per_kwh = self.total_cost / self.energy_added_kwh
        
        self.cost_breakdown = {
            'flat_fee': tariff.flat_fee,
            'energy_cost': self.energy_delivered_kwh * tariff.energy_rate,
            'time_cost': self.total_time_minutes * tariff.time_rate,
        }
        
        return self
    
    def summary(self) -> str:
        """Generate human-readable summary"""
        summary = f"""
Charging Session Summary
========================
Vehicle: {self.parameters.vehicle.name}
Charger: {self.parameters.charger.name}
SoC: {self.parameters.start_soc:.0f}% → {self.parameters.target_soc:.0f}%

Results:
--------
Duration:        {self.total_time_minutes:.1f} minutes ({self.total_time_minutes/60:.2f} hours)
Energy Added:    {self.energy_added_kwh:.2f} kWh
Energy from Grid: {self.energy_delivered_kwh:.2f} kWh
Average Power:   {self.average_power_kw:.1f} kW
Peak Power:      {self.peak_power_kw:.1f} kW
Efficiency:      {self.charging_efficiency*100:.1f}%
"""
        
        if self.total_cost is not None:
            summary += f"""
Pricing:
--------
Total Cost:      {self.tariff.currency} {self.total_cost:.2f}
Cost per kWh:    {self.tariff.currency} {self.cost_per_kwh:.3f}/kWh
  - Flat fee:    {self.tariff.currency} {self.cost_breakdown['flat_fee']:.2f}
  - Energy:      {self.tariff.currency} {self.cost_breakdown['energy_cost']:.2f}
  - Time:        {self.tariff.currency} {self.cost_breakdown['time_cost']:.2f}
"""
        return summary.strip()
    
    def plot(self):
        """Generate visualization of power and SoC profiles"""
        import matplotlib.pyplot as plt
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
        
        # Power profile
        ax1.plot(self.time_series, self.power_profile, 'b-', linewidth=2)
        ax1.axhline(self.average_power_kw, color='r', linestyle='--', 
                    label=f'Average: {self.average_power_kw:.1f} kW')
        ax1.set_ylabel('Power (kW)')
        ax1.set_title('Charging Session Profile')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # SoC profile
        ax2.plot(self.time_series, self.soc_profile, 'g-', linewidth=2)
        ax2.set_xlabel('Time (minutes)')
        ax2.set_ylabel('State of Charge (%)')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
```

### **3. Physics Engine** (`sim/physics/charging.py`)

Key calculations needed:

```python
def calculate_charging_session(
    parameters: SessionParameters
) -> SessionResult:
    """
    Simulates a charging session with minute-by-minute resolution.
    
    Args:
        parameters: SessionParameters with all input configuration
    
    Returns:
        SessionResult with complete simulation output including:
        - Total charging time (minutes)
        - Energy added (kWh) and delivered (kWh)
        - Average/peak power (kW)
        - Power, SoC, and time profiles
        - Efficiency metrics
    """
    # Simplified algorithm:
    # 1. Initialize state
    # 2. For each time step:
    #    a. Determine max power (charger, vehicle, curve limits)
    #    b. Calculate energy transferred in time step
    #    c. Update SoC
    #    d. Check if target SoC reached
    # 3. Compile results into SessionResult
    
# Alternative convenience function:
def simulate_session(
    charger: Charger,
    vehicle: Vehicle,
    start_soc: float,
    target_soc: float,
    tariff: Optional[Tariff] = None
) -> SessionResult:
    """Convenience wrapper for quick simulations"""
    params = SessionParameters(
        vehicle=vehicle,
        charger=charger,
        start_soc=start_soc,
        target_soc=target_soc
    )
    result = calculate_charging_session(params)
    
    if tariff:
        result.apply_tariff(tariff)
    
    return result
```

**Core physics:**
1. **Power limiting** - `actual_power = min(charger_max, vehicle_max, curve_limit)`
2. **AC charging**: Power = √3 × Voltage × Current × Power Factor × Efficiency
3. **DC charging**: Follow vehicle's charging curve
4. **Energy accumulation**: E = ∫P(t)dt
5. **SoC updates**: SoC(t) = SoC₀ + E(t) / Battery_Capacity

### **4. Refined Requirements**

**Missing/Additional Parameters:**
- **Charging efficiency** (typically 85-95%)
- **Power factor** for AC charging (usually ~0.99)
- **Ambient temperature** (affects charging curve - optional)
- **Battery temperature limits** (affects DC fast charging - optional)
- **Preconditioning** status (for DC - optional)
- **Time step resolution** (suggest 1-minute intervals)

**Session Parameters to Output:**
- Charging time (total and by phase if multi-phase)
- Energy added (kWh)
- Energy delivered from grid (accounting for losses)
- Average/peak power
- Power profile over time
- **Cost breakdown** (flat fee + time-based + energy-based)
- **Cost per kWh added** (useful metric)

### **5. Integration with Existing Data**

```python
# sim/analysis/pricing.py
def analyze_session_cost(
    session: SessionResult,
    tariff: MobieTariff  # From your existing data
) -> CostAnalysis:
    """
    Calculate total cost based on Mobie tariff structure:
    - FLAT: Fixed per session
    - ENERGY: Per kWh
    - TIME: Per minute
    """
    cost = tariff.flat + 
           (session.energy_kwh * tariff.energy_rate) +
           (session.time_min * tariff.time_rate)
    
    return CostAnalysis(
        total_cost=cost,
        cost_per_kwh=cost / session.energy_kwh,
        breakdown={...}
    )
```

### **6. Statistical Analysis** (`sim/analysis/statistics.py`)

For distribution analysis:
```python
def simulate_session_distribution(
    charger: Charger,
    vehicle_mix: List[Tuple[Vehicle, float]],  # (vehicle, probability)
    soc_distribution: SOCDistribution,
    n_samples: int = 10000
) -> SessionDistribution:
    """
    Monte Carlo simulation for price distribution:
    - Sample from vehicle mix
    - Sample from SoC start/end distribution
    - Calculate costs
    - Return statistical distribution
    """
```

### **7. Implementation Phases**

**Phase 1: Core Models** (Week 1)
- [ ] Create `sim/` package structure
- [ ] Implement `Vehicle`, `Charger`, `ChargingCurve` dataclasses
- [ ] Implement `Tariff` model with Mobie data integration
- [ ] Implement `SessionParameters` and `SessionResult` models
- [ ] Create preset library with common vehicles/chargers

**Phase 2: Physics Engine** (Week 2)
- [ ] Implement AC charging calculations
- [ ] Implement DC charging with curves
- [ ] Add validation and unit tests
- [ ] Create example notebook

**Phase 3: Tariff Integration** (Week 3)
- [ ] Connect with existing Mobie tariff data
- [ ] Implement cost calculation
- [ ] Add support for Spain data

**Phase 4: Statistical Analysis** (Week 4)
- [ ] Monte Carlo simulation for distributions
- [ ] Visualization tools
- [ ] Report generation

### **8. Example Usage**

```python
from sim.models import Vehicle, Charger, Tariff, SessionParameters
from sim.physics.charging import simulate_session
from sim.presets import vehicles, chargers
import pandas as pd

# === Example 1: Basic Simulation ===
vehicle = vehicles.TESLA_MODEL_3_LR
charger = chargers.IONITY_350KW

result = simulate_session(
    charger=charger,
    vehicle=vehicle,
    start_soc=20,
    target_soc=80
)

print(result.summary())
result.plot()  # Visualize power and SoC curves

# === Example 2: With Tariff Integration ===
# Load tariff from Mobie data
mobie_df = pd.read_csv('data/naps/portugal/mobie_tariffs_latest.csv', sep=';')
tariff_data = mobie_df[mobie_df['UID_TOMADA'] == 'PT-EDP-EABF-00008-1-1'].iloc[0]

# Create tariff model
tariff = Tariff(
    id=tariff_data['UID_TOMADA'],
    operator=tariff_data['OPERADOR'],
    flat_fee=0.261,
    energy_rate=0.10,
    time_rate=0.015
)

# Simulate with pricing
result = simulate_session(
    charger=charger,
    vehicle=vehicle,
    start_soc=20,
    target_soc=80,
    tariff=tariff
)

print(f"Total cost: €{result.total_cost:.2f}")
print(f"Cost per kWh: €{result.cost_per_kwh:.3f}")

# === Example 3: Advanced with SessionParameters ===
from sim.models import SessionParameters

params = SessionParameters(
    vehicle=vehicle,
    charger=charger,
    start_soc=15,
    target_soc=85,
    ambient_temp_c=5,  # Cold weather
    preconditioned=False,
    time_step_seconds=30  # Higher resolution
)

from sim.physics.charging import calculate_charging_session
result = calculate_charging_session(params)
result.apply_tariff(tariff)

# === Example 4: Batch Analysis ===
# Simulate multiple scenarios
scenarios = [
    (10, 80),  # Road trip charge
    (20, 80),  # Typical fast charge
    (40, 60),  # Top-up
    (60, 90),  # Extended charge
]

results = []
for start, end in scenarios:
    r = simulate_session(charger, vehicle, start, end, tariff)
    results.append({
        'soc_range': f"{start}-{end}%",
        'time_min': r.total_time_minutes,
        'energy_kwh': r.energy_added_kwh,
        'cost': r.total_cost,
        'cost_per_kwh': r.cost_per_kwh
    })

results_df = pd.DataFrame(results)
print(results_df)
```

### **9. Testing Strategy**

- **Unit tests**: Each calculation function
- **Integration tests**: Full session simulations
- **Validation**: Compare with real-world data (if available)
- **Edge cases**: 0% → 100% charging, very low/high power

### **10. Future Enhancements**

- Temperature effects on charging curve
- Battery degradation over time
- Queue/waiting time simulation
- Route planning integration
- API for web service

---

