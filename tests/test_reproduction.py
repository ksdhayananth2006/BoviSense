"""
Tests for Reproductive Analytics and Breeding Timelines
"""
import datetime
import pytest
from services.reproductive_manager import ReproductiveManager


def test_return_to_estrus_projection():
    """Verify return-to-estrus calculates 21-day window correctly."""
    service_date = "2026-02-01T08:00:00"
    res = ReproductiveManager.calculate_return_to_estrus(service_date, cycle_length_days=21)

    assert res["is_estimate"] is True
    assert res["expected_return_date"] == "2026-02-22"
    assert res["window_start"] == "2026-02-19"  # Day 18
    assert res["window_end"] == "2026-02-25"    # Day 24


def test_calving_due_date_projection():
    """Verify gestation projection based on standard 279-day reference."""
    conception_date = "2026-01-01T00:00:00"
    res = ReproductiveManager.estimate_calving_due_date(conception_date, gestation_days=279)

    # 2026 is not a leap year. 2026-01-01 + 279 days = 2026-10-07
    expected = (datetime.date(2026, 1, 1) + datetime.timedelta(days=279)).isoformat()
    assert res["estimated_due_date"] == expected
    assert "279-day average gestation" in res["disclaimer"]
