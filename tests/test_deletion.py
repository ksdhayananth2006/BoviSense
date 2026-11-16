"""
Tests for Record Deletion Safeguards and Dataset Clearing Operations
"""
import pytest
from database.db_manager import db
from services.dataset_manager import DatasetManager


def test_deletion_safeguard_with_dependencies():
    """Verify that deleting an animal with dependent records is blocked."""
    # COW-001 has sensor observations in the database
    deps = DatasetManager.check_dependencies("animals", "COW-001")
    assert len(deps) > 0, "Expected dependencies for COW-001"

    success, msg = DatasetManager.delete_record("animals", "COW-001")
    assert success is False
    assert "Cannot delete: Dependent records exist" in msg


def test_clear_dataset_preserves_schema():
    """Verify clearing a dataset deletes records while preserving table schema and ability to re-insert."""
    # Insert a dummy environmental observation
    db.execute(
        """
        INSERT OR REPLACE INTO environmental_observations (environment_id, barn_id, timestamp, temperature_c, relative_humidity_pct)
        VALUES ('ENV-CLEAR-TEST', 'BARN-A', '2026-06-01T00:00:00', 22.0, 50.0)
        """
    )
    assert db.get_row_count("environmental_observations") > 0

    # Clear environmental_observations
    success, msg = DatasetManager.clear_dataset("environmental_observations")
    assert success is True
    assert db.get_row_count("environmental_observations") == 0

    # Verify table schema is still intact by inserting a new record
    db.execute(
        """
        INSERT INTO environmental_observations (environment_id, barn_id, timestamp, temperature_c, relative_humidity_pct)
        VALUES ('ENV-POST-CLEAR', 'BARN-A', '2026-06-02T00:00:00', 24.0, 55.0)
        """
    )
    assert db.get_row_count("environmental_observations") == 1


def test_ground_truth_can_be_cleared_independently():
    """Verify educational ground truth can be completely cleared without impacting core system tables."""
    success, msg = DatasetManager.clear_dataset("educational_ground_truth")
    assert success is True
    assert db.get_row_count("educational_ground_truth") == 0

    # System must continue functioning
    assert db.table_exists("animals")
    assert db.table_exists("sensor_observations")
