"""
Tests for Rule-Based Estrus Indication Engine
"""
import pytest
from services.estrus_predictor import EstrusPredictor


def test_estrus_score_surge():
    """Verify strong estrus score when activity surges and mounting occurs."""
    historical = [
        {"animal_id": "COW-TEST", "timestamp": f"2026-01-0{d}T08:00:00", "activity_count": 100.0, "rumination_time_min": 40.0, "standing_time_min": 60.0, "lying_time_min": 100.0, "body_temperature_c": 38.5, "quality_status": "valid"}
        for d in range(1, 8)
    ]

    current_estrus = {
        "animal_id": "COW-TEST",
        "timestamp": "2026-01-08T08:00:00",
        "activity_count": 280.0,              # Massive surge (+180%)
        "rumination_time_min": 15.0,           # Significant drop (-62%)
        "standing_time_min": 150.0,            # Standing time increase
        "standing_to_be_mounted_count": 2,     # Highly specific sign
        "mounts_performed": 3,
        "mounts_received": 2,
        "lying_time_min": 40.0,
        "body_temperature_c": 39.0,
        "quality_status": "valid"
    }

    predictor = EstrusPredictor()
    res = predictor.evaluate_observation(current_estrus, historical)

    assert res["status"] == "calculated"
    assert res["score"] >= 75.0
    assert res["category_key"] in ("Elevated", "Strong")
    assert res["coverage"] >= 0.8


def test_insufficient_evidence_coverage():
    """Verify evaluator reports insufficient data if coverage is below 30%."""
    historical = [
        {"animal_id": "COW-TEST", "timestamp": f"2026-01-0{d}T08:00:00", "activity_count": 100.0, "quality_status": "valid"}
        for d in range(1, 6)
    ]
    # Current has only lying_time which accounts for only 5% of weight
    current_sparse = {
        "animal_id": "COW-TEST",
        "timestamp": "2026-01-06T08:00:00",
        "lying_time_min": 80.0,
        "activity_count": None,
        "rumination_time_min": None
    }
    predictor = EstrusPredictor()
    res = predictor.evaluate_observation(current_sparse, historical)

    assert res["status"] == "insufficient_data"
    assert res["score"] is None
    assert "below minimum requirement" in res["message"]


def test_thi_context_preserved():
    """Verify high THI context notes environmental heat stress without suppressing reproductive evidence."""
    historical = [
        {"animal_id": "COW-TEST", "timestamp": f"2026-01-0{d}T08:00:00", "activity_count": 100.0, "rumination_time_min": 40.0, "quality_status": "valid"}
        for d in range(1, 6)
    ]
    current = {
        "animal_id": "COW-TEST",
        "timestamp": "2026-01-06T08:00:00",
        "activity_count": 220.0,
        "rumination_time_min": 20.0,
        "standing_to_be_mounted_count": 1
    }
    predictor = EstrusPredictor()
    # High thermal stress (THI = 82)
    res = predictor.evaluate_observation(current, historical, thi_context=82.0)

    assert res["status"] == "calculated"
    assert res["score"] >= 50.0
    assert res["thi_note"] is not None
    assert "Thermal stress" in res["thi_note"]
