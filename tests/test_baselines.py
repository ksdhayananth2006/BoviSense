"""
Tests for Baseline Statistical Calculations and Eligibility
"""
import pytest
from services.baseline_calculator import BaselineCalculator


def test_baseline_stats_known_array():
    """Verify mean, std, median, MAD with verified statistical arrays."""
    data = [10.0, 12.0, 14.0, 16.0, 18.0]
    # Mean: 14.0, Std: 3.16, Median: 14.0, MAD: 2.0
    stats = BaselineCalculator.calculate_stats(data)
    assert stats["mean"] == 14.0
    assert stats["median"] == 14.0
    assert stats["mad"] == 2.0
    assert stats["count"] == 5


def test_baseline_eligibility_insufficient_days():
    """Verify minimum valid days requirement rejects baselines with fewer than 3 days."""
    # Only 2 days of observations
    obs = [
        {"timestamp": "2026-01-01T08:00:00", "activity_count": 100.0, "quality_status": "valid"},
        {"timestamp": "2026-01-01T12:00:00", "activity_count": 110.0, "quality_status": "valid"},
        {"timestamp": "2026-01-02T08:00:00", "activity_count": 105.0, "quality_status": "valid"},
    ]
    res = BaselineCalculator.compute_animal_baseline(obs, "activity_count", window_days=14)
    assert res["status"] == "insufficient_data"
    assert res["distinct_days"] == 2


def test_baseline_eligibility_sufficient_days():
    """Verify baseline is marked valid when >= 3 distinct calendar days are present."""
    obs = [
        {"timestamp": "2026-01-01T08:00:00", "activity_count": 100.0, "quality_status": "valid"},
        {"timestamp": "2026-01-02T08:00:00", "activity_count": 105.0, "quality_status": "valid"},
        {"timestamp": "2026-01-03T08:00:00", "activity_count": 110.0, "quality_status": "valid"},
        {"timestamp": "2026-01-04T08:00:00", "activity_count": 108.0, "quality_status": "valid"},
    ]
    res = BaselineCalculator.compute_animal_baseline(obs, "activity_count", window_days=14)
    assert res["status"] == "valid"
    assert res["distinct_days"] == 4
    assert res["stats"]["mean"] > 100.0
