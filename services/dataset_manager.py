"""
BOVISENSE Complete Dataset Management Service
Orchestrates browsing, editing, inserting, deleting, clearing, exporting,
and restoring all 13 primary biological datasets.
"""
import csv
import datetime
import io
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd

from config.settings import PRIMARY_DATASETS, SAMPLE_DATA_DIR
from database.backup_manager import backup_manager
from database.db_manager import db
from services.audit_manager import AuditManager
from services.csv_importer import CSVImporter
from services.data_validator import DATASET_SCHEMAS, DataValidator

logger = logging.getLogger("bovisense.dataset_manager")


DATASET_METADATA: Dict[str, Dict[str, str]] = {
    "animals": {"category": "Herd Management", "desc": "Individual animal profiles, pedigree, and production attributes."},
    "sensor_observations": {"category": "Sensor Data", "desc": "High-frequency activity, rumination, temperature, and feeding records."},
    "environmental_observations": {"category": "Environment", "desc": "Barn ambient temperature, relative humidity, and solar radiation."},
    "reproductive_events": {"category": "Reproduction", "desc": "Estrus visual sightings, examinations, and confirmed biological events."},
    "ai_records": {"category": "Reproduction", "desc": "Artificial insemination service records, technician IDs, and semen lots."},
    "pregnancy_records": {"category": "Reproduction", "desc": "Veterinary pregnancy diagnosis, ultrasound, and gestation estimates."},
    "calving_records": {"category": "Reproduction", "desc": "Parturition events, dam IDs, calving ease, and complication logs."},
    "health_observations": {"category": "Health", "desc": "Clinical symptom monitoring (cough, mastitis signs, lethargy, discharge)."},
    "health_alerts": {"category": "Health", "desc": "System-generated and screening health alerts with veterinary actions."},
    "milk_records": {"category": "Production", "desc": "Milking session and daily milk yields, electrical conductivity, and SCC."},
    "bcs_records": {"category": "Production", "desc": "Periodic body condition scores evaluated on a 1.0 to 5.0 scale."},
    "calf_care_records": {"category": "Youngstock", "desc": "Colostrum quality (Brix %), vaccinations, navel dipping, and care events."},
    "educational_ground_truth": {"category": "Evaluation", "desc": "Independent verified ground-truth labels for academic assessment."}
}


class DatasetManager:
    """Provides high-level dataset administration operations with transactional safety."""

    @staticmethod
    def list_datasets() -> List[Dict[str, Any]]:
        """Returns metadata, row counts, and health status for all 13 primary datasets."""
        result = []
        for name in PRIMARY_DATASETS:
            schema = DATASET_SCHEMAS.get(name, {})
            meta = DATASET_METADATA.get(name, {"category": "Other", "desc": ""})
            count = db.get_row_count(name)
            
            # Query last import or update
            last_import = db.fetchone(
                "SELECT import_datetime FROM import_batches WHERE dataset_name = ? ORDER BY import_datetime DESC LIMIT 1",
                (name,)
            )

            result.append({
                "dataset_name": name,
                "display_name": name.replace("_", " ").title(),
                "category": meta["category"],
                "description": meta["desc"],
                "records": count,
                "columns_count": len(schema.get("columns", [])),
                "primary_key": schema.get("primary_key", "id"),
                "last_import": last_import["import_datetime"] if last_import else "Never"
            })
        return result

    @staticmethod
    def get_records(
        dataset_name: str,
        search_query: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Retrieves paginated records with optional search filter."""
        schema = DATASET_SCHEMAS.get(dataset_name)
        if not schema:
            return [], 0

        pk_col = schema["primary_key"]
        cols = schema["columns"]

        query = f"SELECT * FROM {dataset_name}"
        count_query = f"SELECT COUNT(*) as total FROM {dataset_name}"
        params: List[Any] = []

        if search_query and search_query.strip():
            # Build search clause across text columns
            clauses = []
            for col in cols:
                clauses.append(f"CAST({col} AS TEXT) LIKE ?")
                params.append(f"%{search_query.strip()}%")
            where_sql = f" WHERE {' OR '.join(clauses)}"
            query += where_sql
            count_query += where_sql

        total_row = db.fetchone(count_query, params)
        total = total_row["total"] if total_row else 0

        query += f" ORDER BY {pk_col} DESC LIMIT ? OFFSET ?"
        rows = db.fetchall(query, params + [limit, offset])
        return rows, total

    @staticmethod
    def add_record(dataset_name: str, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validates and adds a single record."""
        is_valid, errors, _ = DataValidator.validate_record(dataset_name, data)
        if not is_valid:
            return False, f"Validation failed: {'; '.join(errors)}"

        schema = DATASET_SCHEMAS[dataset_name]
        pk_col = schema["primary_key"]
        pk_val = data.get(pk_col)

        # Check existing
        existing = db.fetchone(f"SELECT 1 FROM {dataset_name} WHERE {pk_col} = ?", (pk_val,))
        if existing:
            return False, f"Record with {pk_col}='{pk_val}' already exists."

        keys = list(data.keys())
        placeholders = ", ".join(["?"] * len(keys))
        cols = ", ".join(keys)

        try:
            db.execute(f"INSERT INTO {dataset_name} ({cols}) VALUES ({placeholders})", list(data.values()))
            AuditManager.log_action("INSERT_RECORD", dataset_name, str(pk_val), action_summary=f"Added record {pk_val}")
            return True, f"Record {pk_val} added successfully."
        except Exception as e:
            logger.error(f"Failed to add record: {e}")
            return False, f"Database error: {e}"

    @staticmethod
    def update_record(dataset_name: str, pk_val: Any, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validates and updates an existing record."""
        is_valid, errors, _ = DataValidator.validate_record(dataset_name, data)
        if not is_valid:
            return False, f"Validation failed: {'; '.join(errors)}"

        schema = DATASET_SCHEMAS[dataset_name]
        pk_col = schema["primary_key"]

        set_clause = ", ".join([f"{k} = ?" for k in data.keys() if k != pk_col])
        params = [data[k] for k in data.keys() if k != pk_col] + [pk_val]

        try:
            updated = db.execute(f"UPDATE {dataset_name} SET {set_clause} WHERE {pk_col} = ?", params)
            if updated > 0:
                AuditManager.log_action("UPDATE_RECORD", dataset_name, str(pk_val), action_summary=f"Updated record {pk_val}")
                return True, f"Record {pk_val} updated successfully."
            return False, f"Record with {pk_col}='{pk_val}' not found."
        except Exception as e:
            return False, f"Database error: {e}"

    @staticmethod
    def check_dependencies(dataset_name: str, pk_val: Any) -> List[str]:
        """Checks for foreign key references before deleting a record."""
        dependencies = []
        if dataset_name == "animals":
            # Check sensor observations, repro events, weights, calvings, etc.
            obs = db.fetchone("SELECT COUNT(*) as c FROM sensor_observations WHERE animal_id = ?", (pk_val,))
            if obs and obs["c"] > 0:
                dependencies.append(f"{obs['c']} sensor observation(s)")
            repro = db.fetchone("SELECT COUNT(*) as c FROM reproductive_events WHERE animal_id = ?", (pk_val,))
            if repro and repro["c"] > 0:
                dependencies.append(f"{repro['c']} reproductive event(s)")
            calvings = db.fetchone("SELECT COUNT(*) as c FROM calving_records WHERE dam_id = ?", (pk_val,))
            if calvings and calvings["c"] > 0:
                dependencies.append(f"{calvings['c']} calving record(s) where animal is dam")
            offspring = db.fetchone("SELECT COUNT(*) as c FROM animals WHERE dam_id = ? OR sire_id = ?", (pk_val, pk_val))
            if offspring and offspring["c"] > 0:
                dependencies.append(f"{offspring['c']} offspring animal(s)")
        return dependencies

    @staticmethod
    def delete_record(dataset_name: str, pk_val: Any) -> Tuple[bool, str]:
        """Safely deletes an individual record after checking dependencies."""
        deps = DatasetManager.check_dependencies(dataset_name, pk_val)
        if deps:
            return False, f"Cannot delete: Dependent records exist ({', '.join(deps)}). Remove or reassign them first."

        schema = DATASET_SCHEMAS[dataset_name]
        pk_col = schema["primary_key"]

        try:
            deleted = db.execute(f"DELETE FROM {dataset_name} WHERE {pk_col} = ?", (pk_val,))
            if deleted > 0:
                AuditManager.log_action("DELETE_RECORD", dataset_name, str(pk_val), action_summary=f"Deleted record {pk_val}")
                return True, f"Record {pk_val} deleted successfully."
            return False, f"Record {pk_val} not found."
        except Exception as e:
            return False, f"Deletion failed: {e}"

    @staticmethod
    def delete_selected(dataset_name: str, pk_values: List[Any]) -> Tuple[int, List[str]]:
        """Deletes a batch of records, collecting any errors."""
        deleted_count = 0
        errors = []
        for pk in pk_values:
            success, msg = DatasetManager.delete_record(dataset_name, pk)
            if success:
                deleted_count += 1
            else:
                errors.append(msg)
        return deleted_count, errors

    @staticmethod
    def clear_dataset(dataset_name: str) -> Tuple[bool, str]:
        """
        Completely clears records from a primary dataset while preserving table schema!
        Creates an automatic safety backup beforehand.
        """
        if dataset_name not in PRIMARY_DATASETS:
            return False, f"Table '{dataset_name}' is not an authorized primary dataset."

        # Check if animal dataset has dependents
        if dataset_name == "animals":
            total_sensors = db.get_row_count("sensor_observations")
            total_repro = db.get_row_count("reproductive_events")
            if total_sensors > 0 or total_repro > 0:
                return False, (
                    f"Cannot clear 'animals' while dependent records exist "
                    f"({total_sensors} sensor observations, {total_repro} reproductive events). "
                    "Clear dependent datasets first."
                )

        try:
            # 1. Take safety backup
            backup_manager.create_backup(f"pre_clear_{dataset_name}")

            # 2. Delete all records within transaction
            with db.transaction() as conn:
                conn.execute(f"DELETE FROM {dataset_name}")

            AuditManager.log_action(
                action_type="CLEAR_DATASET",
                dataset_name=dataset_name,
                action_summary=f"Cleared all records from {dataset_name}. Schema preserved.",
                result_status="SUCCESS"
            )
            return True, f"Successfully cleared all records from {dataset_name}."
        except Exception as e:
            logger.error(f"Clear dataset failed: {e}")
            return False, f"Failed to clear dataset: {e}"

    @staticmethod
    def export_csv(dataset_name: str) -> str:
        """Exports dataset records as CSV string with formula injection protection."""
        schema = DATASET_SCHEMAS.get(dataset_name)
        if not schema:
            return ""

        rows = db.fetchall(f"SELECT * FROM {dataset_name}")
        if not rows:
            # Return headers only
            return ",".join(schema["columns"]) + "\n"

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=schema["columns"])
        writer.writeheader()

        for r in rows:
            clean_row = {}
            for col in schema["columns"]:
                val = r.get(col, "")
                clean_row[col] = CSVImporter.sanitize_for_export(val)
            writer.writerow(clean_row)

        return output.getvalue()

    @staticmethod
    def restore_sample_dataset(dataset_name: str) -> Tuple[bool, str]:
        """Restores standard sample data for a specific dataset from data/sample/."""
        sample_file = SAMPLE_DATA_DIR / f"{dataset_name}.csv"
        if not sample_file.exists():
            return False, f"Sample file not found at {sample_file}"

        with open(sample_file, "r", encoding="utf-8") as f:
            content = f.read()

        result = CSVImporter.execute_import(
            file_content=content,
            dataset_name=dataset_name,
            import_policy="Replace",
            filename=sample_file.name
        )

        if result["success"]:
            return True, f"Successfully restored {result['inserted']} sample records for {dataset_name}."
        return False, f"Failed to restore sample data: {result['message']}"

    @staticmethod
    def restore_all_samples() -> Dict[str, Any]:
        """Restores sample data across all 13 primary datasets in relational order."""
        # Clear existing data in reverse dependency order
        reverse_clear_order = [
            "educational_ground_truth",
            "calf_care_records",
            "bcs_records",
            "milk_records",
            "health_alerts",
            "health_observations",
            "calving_records",
            "pregnancy_records",
            "ai_records",
            "reproductive_events",
            "environmental_observations",
            "sensor_observations",
            "animals"
        ]
        supporting_dependent_tables = [
            "calving_calf_links",
            "animal_weight_records",
            "animal_location_history",
            "prediction_results",
            "lactation_records"
        ]
        with db.transaction() as conn:
            for s in supporting_dependent_tables:
                conn.execute(f"DELETE FROM {s}")
            for ds in reverse_clear_order:
                if ds == "animals":
                    conn.execute("UPDATE animals SET dam_id = NULL, sire_id = NULL")
                conn.execute(f"DELETE FROM {ds}")

        db.seed_supporting_tables()

        ordered_datasets = [
            "animals",
            "sensor_observations",
            "environmental_observations",
            "reproductive_events",
            "ai_records",
            "pregnancy_records",
            "calving_records",
            "health_observations",
            "health_alerts",
            "milk_records",
            "bcs_records",
            "calf_care_records",
            "educational_ground_truth"
        ]
        results = {}
        for ds in ordered_datasets:
            success, msg = DatasetManager.restore_sample_dataset(ds)
            results[ds] = {"success": success, "message": msg}
        return results
