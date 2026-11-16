"""
Tests for BOVISENSE Database Integrity and Foreign Key Enforcement
"""
import pytest
import sqlite3
from database.db_manager import db


def test_foreign_key_enforcement():
    """Verify that SQLite foreign-key enforcement is strictly active."""
    # Attempting to insert a sensor observation for a non-existent animal must fail
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            """
            INSERT INTO sensor_observations (observation_id, animal_id, timestamp)
            VALUES ('OBS-FAIL-01', 'NON-EXISTENT-ANIMAL-ID', '2026-01-01T00:00:00')
            """
        )


def test_unique_constraint():
    """Verify that primary key duplication is rejected."""
    # Find an existing animal ID
    row = db.fetchone("SELECT animal_id FROM animals LIMIT 1")
    if row:
        a_id = row["animal_id"]
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                f"""
                INSERT INTO animals (animal_id, animal_type, sex, breed, dob)
                VALUES ('{a_id}', 'cow', 'F', 'Holstein', '2022-01-01')
                """
            )


def test_transaction_rollback():
    """Verify that an error in a transaction causes a full rollback."""
    initial_count = db.get_row_count("barns")
    try:
        with db.transaction() as conn:
            conn.execute("INSERT INTO barns (barn_id, barn_name) VALUES ('TEST-B1', 'Test Barn 1')")
            # Force an error
            conn.execute("INSERT INTO barns (barn_id, barn_name) VALUES ('TEST-B1', 'Duplicate')")
    except Exception:
        pass

    # Count must remain unchanged
    after_count = db.get_row_count("barns")
    assert after_count == initial_count


def test_biological_check_constraints():
    """Verify check constraints prevent self-parenting and invalid humidity."""
    # Animal cannot be its own dam
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            """
            INSERT INTO animals (animal_id, animal_type, sex, breed, dob, dam_id)
            VALUES ('COW-SELF', 'cow', 'F', 'Holstein', '2022-01-01', 'COW-SELF')
            """
        )

    # Relative humidity must be between 0 and 100%
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            """
            INSERT INTO environmental_observations (environment_id, timestamp, temperature_c, relative_humidity_pct)
            VALUES ('ENV-FAIL', '2026-01-01T00:00:00', 25.0, 150.0)
            """
        )
