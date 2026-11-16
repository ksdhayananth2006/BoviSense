"""
Tests for Temperature-Humidity Index (THI) Calculations
"""
import pytest
from services.thi_calculator import THICalculator


def test_thi_calculation_known_values():
    """Verify NRC (1971) formula with known analytical values."""
    # T = 25.0 °C, RH = 50.0 % -> 71.78
    thi = THICalculator.calculate_thi(25.0, 50.0)
    assert thi == 71.78

    # T = 35.0 °C, RH = 70.0 % -> 88.89
    thi_hot = THICalculator.calculate_thi(35.0, 70.0)
    assert thi_hot == 88.89

    # T = 15.0 °C, RH = 40.0 % -> thermoneutral low
    thi_cool = THICalculator.calculate_thi(15.0, 40.0)
    assert thi_cool < 68.0


def test_thi_classification():
    """Verify stress band classifications."""
    assert THICalculator.classify_thi(65.0)[0] == "Low"
    assert THICalculator.classify_thi(69.5)[0] == "Mild"
    assert THICalculator.classify_thi(75.2)[0] == "Moderate"
    assert THICalculator.classify_thi(81.0)[0] == "Severe"
    assert THICalculator.classify_thi(86.4)[0] == "Extreme"


def test_thi_bounds_validation():
    """Verify invalid humidity values are rejected."""
    with pytest.raises(ValueError):
        THICalculator.calculate_thi(25.0, 105.0)

    with pytest.raises(ValueError):
        THICalculator.calculate_thi(25.0, -5.0)


def test_thi_discrepancy():
    """Verify discrepancy detector flags divergence > 0.5 units."""
    calc_thi = 72.0
    assert not THICalculator.check_thi_discrepancy(72.2, calc_thi, tolerance=0.5)
    assert THICalculator.check_thi_discrepancy(73.5, calc_thi, tolerance=0.5)
