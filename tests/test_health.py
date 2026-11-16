"""
Tests for Cattle Health Screening and Alert Deduplication
"""
import pytest
from database.repositories import HealthRepository
from services.health_monitor import HealthMonitor


def test_fever_screening_adult_vs_calf():
    """Verify fever cutoff distinguishes adult cattle (39.5°C) from calves (39.8°C)."""
    monitor = HealthMonitor()

    # Adult with 39.6°C -> should trigger alert
    obs_adult = {"body_temperature_c": 39.6, "timestamp": "2026-05-01T10:00:00"}
    alerts_adult = monitor.screen_health_observation("COW-001", obs_adult, is_calf=False)
    fever_adult = [a for a in alerts_adult if a["alert_category"] == "fever_screening"]
    assert len(fever_adult) == 1
    assert fever_adult[0]["priority"] == "medium"

    # Calf with 39.6°C -> physiological normal, should NOT trigger fever
    obs_calf = {"body_temperature_c": 39.6, "timestamp": "2026-05-01T10:00:00"}
    alerts_calf = monitor.screen_health_observation("CALF-001", obs_calf, is_calf=True)
    fever_calf = [a for a in alerts_calf if a["alert_category"] == "fever_screening"]
    assert len(fever_calf) == 0


def test_alert_deduplication():
    """Verify that an animal with an existing unresolved alert is not flooded with duplicate alerts."""
    monitor = HealthMonitor()
    animal_id = "COW-002"

    # First fever observation triggers alert
    obs = {"body_temperature_c": 40.1, "timestamp": "2026-05-01T08:00:00"}
    first_run = monitor.screen_health_observation(animal_id, obs, is_calf=False)
    assert len(first_run) >= 1

    # Second observation 2 hours later with persistent fever
    obs_later = {"body_temperature_c": 40.0, "timestamp": "2026-05-01T10:00:00"}
    second_run = monitor.screen_health_observation(animal_id, obs_later, is_calf=False)

    # Must be deduplicated: no new active fever alert created while unresolved
    fever_second = [a for a in second_run if a["alert_category"] == "fever_screening"]
    assert len(fever_second) == 0


def test_mastitis_screening():
    """Verify mastitis screening flags elevated SCC and abnormal milk."""
    monitor = HealthMonitor()
    obs_mast = {
        "somatic_cell_count": 450000.0,
        "abnormal_milk": 1,
        "udder_swelling": 1,
        "timestamp": "2026-05-01T06:00:00"
    }
    alerts = monitor.screen_health_observation("COW-003", obs_mast)
    mast_alert = [a for a in alerts if a["alert_category"] == "mastitis_screening"]
    assert len(mast_alert) == 1
    assert mast_alert[0]["priority"] in ("high", "critical")
