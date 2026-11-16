"""
Tests for Calf Growth (ADG), Colostrum Brix Refractometry, and Milk Aggregation
"""
import pytest
from services.calf_monitor import CalfMonitor
from services.milk_analyzer import MilkAnalyzer


def test_adg_calculation():
    """Verify Average Daily Gain (kg/day) calculation."""
    # Birth weight: 36.0 kg, Weaning weight: 78.0 kg over 60 days
    # Gain: 42.0 kg / 60 days = 0.700 kg/day
    adg = CalfMonitor.calculate_adg(36.0, 78.0, 60)
    assert adg == 0.7

    # Zero or negative days must return None
    assert CalfMonitor.calculate_adg(36.0, 78.0, 0) is None
    assert CalfMonitor.calculate_adg(36.0, 78.0, -5) is None


def test_colostrum_brix_classification():
    """Verify colostrum quality bands based on optical/digital Brix refractometry."""
    # Brix >= 22% -> High quality
    assert CalfMonitor.evaluate_colostrum_brix(24.5)["status"] == "Good"
    # Brix between 18 and 21.9% -> Borderline
    assert CalfMonitor.evaluate_colostrum_brix(19.0)["status"] == "Borderline"
    # Brix < 18% -> Poor (Risk of FPT)
    assert CalfMonitor.evaluate_colostrum_brix(15.0)["status"] == "Poor"


def test_milk_aggregation_no_double_counting():
    """Verify that milking sessions and daily total records are not double-counted."""
    records = [
        # Day 1: Session records (Morning: 14L, Evening: 11L) -> Total 25L
        {"record_datetime": "2026-03-01T06:00:00", "record_type": "session", "morning_yield_l": 14.0, "total_yield_l": 14.0, "somatic_cell_count": 120000.0},
        {"record_datetime": "2026-03-01T17:00:00", "record_type": "session", "evening_yield_l": 11.0, "total_yield_l": 11.0, "somatic_cell_count": 130000.0},
        # Day 2: Pre-aggregated daily total record (Total 28L)
        {"record_datetime": "2026-03-02T18:00:00", "record_type": "daily_total", "total_yield_l": 28.0, "somatic_cell_count": 150000.0}
    ]

    daily_df = MilkAnalyzer.aggregate_daily_yields(records)
    assert len(daily_df) == 2

    # Check Day 1 total
    day1_row = daily_df[daily_df["date"] == "2026-03-01"]
    assert float(day1_row["total_yield_l"].iloc[0]) == 25.0
    assert float(day1_row["avg_scc"].iloc[0]) == 125000.0

    # Check Day 2 total
    day2_row = daily_df[daily_df["date"] == "2026-03-02"]
    assert float(day2_row["total_yield_l"].iloc[0]) == 28.0
