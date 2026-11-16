"""
Tests for CSV Importer, Policies, Validation, and Formula Injection Sanitization
"""
import io
import pytest
from database.db_manager import db
from services.csv_importer import CSVImporter


def test_csv_preflight_inspection():
    """Verify CSV header analysis and missing column detection."""
    valid_csv = "animal_id,animal_type,sex,breed,dob\nCOW-TST1,cow,F,Jersey,2023-01-01\n"
    info = CSVImporter.inspect_file(valid_csv, "animals")
    assert info["has_primary_key"] is True
    assert len(info["missing_required"]) == 0
    assert info["row_count"] == 1

    # Incomplete CSV missing required columns
    bad_csv = "animal_id,animal_name\nCOW-TST1,Daisy\n"
    info_bad = CSVImporter.inspect_file(bad_csv, "animals")
    assert len(info_bad["missing_required"]) > 0


def test_csv_import_policies():
    """Verify Append, Update, and Skip duplicate policies."""
    test_csv = (
        "animal_id,animal_type,sex,breed,dob,animal_name\n"
        "COW-IMP-01,cow,F,Holstein,2023-01-01,InitialName\n"
    )
    # 1. Initial Insert
    res1 = CSVImporter.execute_import(test_csv, "animals", import_policy="Append", filename="test.csv")
    assert res1["success"] is True
    assert res1["inserted"] == 1

    # 2. Skip duplicates policy
    res2 = CSVImporter.execute_import(test_csv, "animals", import_policy="Skip duplicates", filename="test.csv")
    assert res2["success"] is True
    assert res2["skipped"] == 1
    assert res2["inserted"] == 0

    # 3. Update existing policy
    update_csv = (
        "animal_id,animal_type,sex,breed,dob,animal_name\n"
        "COW-IMP-01,cow,F,Holstein,2023-01-01,UpdatedName\n"
    )
    res3 = CSVImporter.execute_import(update_csv, "animals", import_policy="Update existing", filename="test.csv")
    assert res3["success"] is True
    assert res3["updated"] == 1

    # Check updated value in DB
    row = db.fetchone("SELECT animal_name FROM animals WHERE animal_id = 'COW-IMP-01'")
    assert row["animal_name"] == "UpdatedName"


def test_csv_formula_injection_sanitization():
    """Verify CSV formula injection prefixes (=, +, -, @) are sanitized with a leading single quote."""
    assert CSVImporter.sanitize_for_export("=SUM(A1:A10)") == "'=SUM(A1:A10)"
    assert CSVImporter.sanitize_for_export("+cmd|' /C calc'!A0") == "'+cmd|' /C calc'!A0"
    assert CSVImporter.sanitize_for_export("-2+3*cmd") == "'-2+3*cmd"
    assert CSVImporter.sanitize_for_export("@SUM(1,2)") == "'@SUM(1,2)"
    assert CSVImporter.sanitize_for_export("SafeText") == "SafeText"
    assert CSVImporter.sanitize_for_export(42.5) == 42.5
