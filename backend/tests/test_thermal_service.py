"""
Tests for the thermal stress index calculation.
Formula: stress += max(0, battery_temp - 35) × duration_hours
"""

import pytest
from app.services.thermal_service import calculate_thermal_stress_increment, THERMAL_BASELINE_CELSIUS


def test_stress_increment_above_baseline():
    """Temperature above 35°C should accumulate stress."""
    # 46°C for 30 minutes = (46-35) × 0.5 = 5.5 degree-hours
    increment = calculate_thermal_stress_increment(
        battery_temp_celsius=46.0,
        duration_hours=0.5,
    )
    assert abs(increment - 5.5) < 0.001, f"Expected 5.5, got {increment}"


def test_stress_increment_at_baseline():
    """Temperature exactly at 35°C should produce zero stress."""
    increment = calculate_thermal_stress_increment(
        battery_temp_celsius=35.0,
        duration_hours=1.0,
    )
    assert increment == 0.0, f"Expected 0.0 at baseline, got {increment}"


def test_stress_increment_below_baseline():
    """Temperature below 35°C should produce zero stress (not negative)."""
    increment = calculate_thermal_stress_increment(
        battery_temp_celsius=28.0,  # cool battery (charging at night)
        duration_hours=2.0,
    )
    assert increment == 0.0, f"Expected 0.0 below baseline, got {increment}"


def test_stress_accumulation_thermal_event():
    """
    Simulate the KA01AB5678 thermal scenario:
    Battery at 46°C for 2 hours during noon fast-charge.
    Expected: (46-35) × 2 = 22 degree-hours
    """
    total_stress = 0.0
    # 2 hours at 46°C (noon fast-charge thermal event)
    for _ in range(120):  # 120 one-minute intervals
        total_stress += calculate_thermal_stress_increment(46.0, 1/60)

    assert abs(total_stress - 22.0) < 0.1, f"Expected ~22.0 degree-hours, got {total_stress:.2f}"


def test_stress_baseline_is_35():
    """Verify the thermal comfort baseline is 35°C as documented."""
    assert THERMAL_BASELINE_CELSIUS == 35.0, (
        f"Thermal baseline must be 35°C per specification. Got {THERMAL_BASELINE_CELSIUS}"
    )


def test_critical_threshold_46c():
    """Test that 46°C is correctly identified as above warning but below critical."""
    from app.config import settings
    assert 46.0 >= settings.THERMAL_WARNING_THRESHOLD, "46°C should trigger warning"
    assert 46.0 < settings.THERMAL_CRITICAL_THRESHOLD, "46°C should NOT trigger critical alert"
    assert 49.0 >= settings.THERMAL_CRITICAL_THRESHOLD, "49°C should trigger critical alert"
