"""
Tests for Schema Versioning and Migration Management
"""
import pytest
from database.db_manager import db
from database.migrations import MigrationManager


def test_schema_version_tracking():
    """Verify that current schema version is properly registered in schema_versions table."""
    mgr = MigrationManager(db)
    ver = mgr.get_current_version()
    assert ver == "2.0.0"


def test_migration_idempotency():
    """Verify applying migrations when on latest version returns empty list without error."""
    mgr = MigrationManager(db)
    applied = mgr.apply_migrations()
    assert applied == []
