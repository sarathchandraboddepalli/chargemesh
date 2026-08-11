"""
ChargeMesh — Battery Degradation Model
Capacity fade model based on cycle count, temperature stress, and depth of discharge.

Model basis: Empirical LFP/NMC capacity fade literature calibrated for Indian commercial EV conditions.
This model is conservative by design — underestimating degradation means BaaS vendors lose money.

SoH Formula:
  SoH (%) = 100 - (cycle_degradation + thermal_degradation + dod_degradation)

  cycle_degradation = cycle_count × base_rate_per_cycle
    - LFP batteries: ~0.025% per cycle (conservative)
    - NMC batteries: ~0.05% per cycle (conservative)

  thermal_degradation = accumulated_thermal_stress × thermal_degradation_per_stress_unit
    - 0.01% SoH per degree-hour above 35°C (Arrhenius-based approximation)

  dod_degradation = additional factor if battery regularly depleted below 15% SoC
    - Shallow cycling (20-80% SoC): minimal degradation
    - Deep cycling (< 10% SoC): accelerated degradation

NOTE: This model requires calibration with real operational data.
The 6-month data collection target (from ideadoc5.md) should be used to refine these coefficients.
"""

from typing import Optional

# Degradation rates per battery chemistry
CHEMISTRY_RATES = {
    "lfp": {
        "base_rate_per_cycle": 0.025,        # % SoH per cycle
        "thermal_stress_rate": 0.01,          # % SoH per degree-hour
        "deep_discharge_penalty": 0.05,       # % SoH per deep discharge event
    },
    "nmc": {
        "base_rate_per_cycle": 0.05,
        "thermal_stress_rate": 0.012,
        "deep_discharge_penalty": 0.08,
    },
    "default": {
        "base_rate_per_cycle": 0.04,          # conservative default
        "thermal_stress_rate": 0.011,
        "deep_discharge_penalty": 0.06,
    },
}


def estimate_soh(
    cycle_count: int,
    accumulated_thermal_stress: float,
    deep_discharge_count: int = 0,
    chemistry: str = "default",
) -> float:
    """
    Estimate current State of Health.

    Args:
        cycle_count: Number of charge/discharge cycles
        accumulated_thermal_stress: Cumulative degree-hours above 35°C
        deep_discharge_count: Number of times discharged below 15% SoC
        chemistry: "lfp", "nmc", or "default"

    Returns:
        Estimated SoH as percentage (0-100)
    """
    rates = CHEMISTRY_RATES.get(chemistry, CHEMISTRY_RATES["default"])

    cycle_loss = cycle_count * rates["base_rate_per_cycle"]
    thermal_loss = accumulated_thermal_stress * rates["thermal_stress_rate"]
    deep_discharge_loss = deep_discharge_count * rates["deep_discharge_penalty"]

    estimated_soh = max(0.0, 100.0 - cycle_loss - thermal_loss - deep_discharge_loss)
    return round(estimated_soh, 2)


def estimate_degradation_from_kwh(
    kwh_consumed: float,
    thermal_stress: float,
    cycle_count: int,
    chemistry: str = "default",
) -> float:
    """
    Estimate SoH degradation attributable to a single battery session.

    Used in BaaS settlement calculation to determine degradation cost.

    Args:
        kwh_consumed: Energy consumed in this session (kWh)
        thermal_stress: Accumulated thermal stress at start of session (degree-hours)
        cycle_count: Current cycle count
        chemistry: Battery chemistry type

    Returns:
        Estimated SoH degradation percentage for this session
    """
    rates = CHEMISTRY_RATES.get(chemistry, CHEMISTRY_RATES["default"])

    # Each full charge cycle ≈ battery_capacity kWh
    # Approximate cycle fraction from kWh
    # Standard assumption: 3 kWh nominal capacity for Indian 2W EVs
    nominal_capacity = 3.5  # kWh
    cycle_fraction = kwh_consumed / nominal_capacity

    # Base degradation from this cycle fraction
    cycle_degradation = cycle_fraction * rates["base_rate_per_cycle"]

    # Thermal degradation multiplier: high thermal stress accelerates degradation
    # At stress > 100 degree-hours, additional 20% degradation acceleration
    thermal_multiplier = 1.0 + (min(thermal_stress, 500) / 1000)
    adjusted_degradation = cycle_degradation * thermal_multiplier

    return round(adjusted_degradation, 4)


def project_remaining_useful_life(
    current_soh: float,
    cycle_count: int,
    daily_cycles: float = 1.0,
    chemistry: str = "default",
) -> float:
    """
    Project remaining battery life in months.

    Args:
        current_soh: Current state of health (%)
        cycle_count: Current cycle count
        daily_cycles: Average charge cycles per day
        chemistry: Battery chemistry

    Returns:
        Estimated months until SoH reaches 70% (end of commercial life)
    """
    END_OF_LIFE_SOH = 70.0
    if current_soh <= END_OF_LIFE_SOH:
        return 0.0

    rates = CHEMISTRY_RATES.get(chemistry, CHEMISTRY_RATES["default"])
    soh_remaining = current_soh - END_OF_LIFE_SOH
    cycles_remaining = soh_remaining / rates["base_rate_per_cycle"]
    days_remaining = cycles_remaining / daily_cycles
    months_remaining = days_remaining / 30

    return round(months_remaining, 1)
