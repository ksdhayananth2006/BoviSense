"""
Tests for Complete Dataset Management Operations Across All 13 Primary Datasets
"""
import pytest
from config.settings import PRIMARY_DATASETS
from services.dataset_manager import DatasetManager


def test_all_13_datasets_cataloged():
    """Verify that all 13 primary datasets are cataloged and manageable."""
    datasets = DatasetManager.list_datasets()
    assert len(datasets) == 13

    names = [d["dataset_name"] for d in datasets]
    for p in PRIMARY_DATASETS:
        assert p in names


def test_add_and_update_record():
    """Verify manual record addition and subsequent update."""
    rec = {
        "bcs_record_id": "BCS-TEST-009",
        "animal_id": "COW-001",
        "assessment_date": "2026-05-15",
        "bcs_value": 3.25,
        "assessor": "Dr. Sharma",
        "assessment_method": "visual",
        "lactation_stage": "mid",
        "body_weight_kg": 590.0,
        "remarks": "Initial"
    }
    success, msg = DatasetManager.add_record("bcs_records", rec)
    assert success is True

    # Update
    rec_update = rec.copy()
    rec_update["remarks"] = "Updated note"
    success_up, msg_up = DatasetManager.update_record("bcs_records", "BCS-TEST-009", rec_update)
    assert success_up is True

    # Delete
    success_del, msg_del = DatasetManager.delete_record("bcs_records", "BCS-TEST-009")
    assert success_del is True


def test_export_csv_has_headers():
    """Verify CSV export produces headers even for empty or populated datasets."""
    csv_str = DatasetManager.export_csv("animals")
    assert "animal_id" in csv_str
    assert "dob" in csv_str
