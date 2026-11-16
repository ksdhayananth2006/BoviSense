"""
Tests for Database Backup and Point-in-Time Restoration
"""
import pytest
from database.backup_manager import BackupManager
from database.db_manager import db


def test_backup_creation_and_integrity():
    """Verify online backup is created and passes PRAGMA integrity_check."""
    mgr = BackupManager()
    backup_path = mgr.create_backup("test_point_in_time")

    assert backup_path.exists()
    assert backup_path.stat().st_size > 0

    backups = mgr.list_backups()
    assert len(backups) > 0
    assert any(b["filename"] == backup_path.name for b in backups)


def test_backup_restore():
    """Verify database can be restored from an existing backup snapshot."""
    mgr = BackupManager()
    backup_path = mgr.create_backup("pre_restore_test")

    # Insert a temporary marker row
    db.execute("INSERT OR REPLACE INTO barns (barn_id, barn_name) VALUES ('BARN-TEMP-DEL', 'Temporary')")
    assert db.fetchone("SELECT barn_id FROM barns WHERE barn_id = 'BARN-TEMP-DEL'") is not None

    # Restore from the backup created before BARN-TEMP-DEL existed
    restored = mgr.restore_backup(backup_path)
    assert restored is True

    # Marker row must no longer be present
    assert db.fetchone("SELECT barn_id FROM barns WHERE barn_id = 'BARN-TEMP-DEL'") is None
