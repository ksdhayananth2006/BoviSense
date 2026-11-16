"""
BOVISENSE Safe CSV Importer Service
Handles transactional CSV parsing, validation, column mapping, idempotency, and audit logging.
"""
import csv
import datetime
import io
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd

from config.settings import CSV_FORMULA_PREFIXES
from database.db_manager import db
from services.audit_manager import AuditManager
from services.data_validator import DATASET_SCHEMAS, DataValidator

logger = logging.getLogger("bovisense.importer")


class CSVImporter:
    """Manages transactional importing and pre-flight validation of CSV files."""

    @staticmethod
    def inspect_file(
        file_content: Union[str, bytes],
        dataset_name: str,
        filename: str = "uploaded.csv"
    ) -> Dict[str, Any]:
        """
        Parses CSV headers and runs pre-flight checks without mutating the database.
        Returns detailed summary: columns, counts, and sample parsed records.
        """
        schema = DataValidator.get_schema(dataset_name)
        if not schema:
            raise ValueError(f"Unknown dataset name: {dataset_name}")

        if isinstance(file_content, bytes):
            # Decode with UTF-8 fallback
            try:
                text = file_content.decode("utf-8")
            except UnicodeDecodeError:
                text = file_content.decode("latin-1")
        else:
            text = file_content

        df = pd.read_csv(io.StringIO(text))
        received_cols = list(df.columns)
        primary_key = schema["primary_key"]

        # Check required columns
        missing_required = [c for c in schema["required"] if c not in received_cols]

        return {
            "filename": filename,
            "row_count": len(df),
            "columns_found": received_cols,
            "expected_columns": schema["columns"],
            "missing_required": missing_required,
            "has_primary_key": primary_key in received_cols,
            "primary_key": primary_key,
            "preview_df": df.head(5)
        }

    @staticmethod
    def execute_import(
        file_content: Union[str, bytes],
        dataset_name: str,
        import_policy: str = "Append",  # "Append", "Update existing", "Replace", "Skip duplicates", "Reject duplicates"
        filename: str = "uploaded.csv"
    ) -> Dict[str, Any]:
        """
        Executes import within an atomic database transaction.
        Rolls back automatically on failure.
        """
        schema = DataValidator.get_schema(dataset_name)
        if not schema:
            raise ValueError(f"Unknown dataset name: {dataset_name}")

        if isinstance(file_content, bytes):
            try:
                text = file_content.decode("utf-8")
            except UnicodeDecodeError:
                text = file_content.decode("latin-1")
        else:
            text = file_content

        df = pd.read_csv(io.StringIO(text))
        # Fill NaN with None for database compatibility
        records = df.where(pd.notnull(df), None).to_dict(orient="records")

        pk_col = schema["primary_key"]
        allowed_cols = schema["columns"]

        inserted = 0
        updated = 0
        skipped = 0
        rejected = 0
        rejection_reasons = []

        import_batch_id = f"imp_{uuid.uuid4().hex[:12]}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Pre-validate all records
        validated_records = []
        for idx, rec in enumerate(records):
            # Filter rec to only known schema columns
            clean_rec = {k: rec[k] for k in allowed_cols if k in rec}
            
            # Format empty strings as None
            for k, v in clean_rec.items():
                if isinstance(v, str) and v.strip() == "":
                    clean_rec[k] = None

            is_valid, errors, warnings = DataValidator.validate_record(dataset_name, clean_rec)
            if not is_valid:
                rejected += 1
                rejection_reasons.append(f"Row {idx+1} ({clean_rec.get(pk_col, 'unknown')}): {'; '.join(errors)}")
            else:
                validated_records.append(clean_rec)

        if import_policy == "Reject duplicates" and rejected > 0:
            # Abort if strict rejection policy is active
            status = "FAILED"
            summary = f"Aborted: {rejected} invalid rows detected under strict policy."
            # Log failed batch
            db.execute(
                """
                INSERT INTO import_batches (
                    import_batch_id, dataset_name, original_filename, import_datetime,
                    import_operation, records_received, records_inserted, records_updated,
                    records_skipped, records_rejected, import_status, validation_summary
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (import_batch_id, dataset_name, filename, now, import_policy, len(records), 0, 0, 0, rejected, status, summary)
            )
            return {
                "success": False,
                "batch_id": import_batch_id,
                "records_received": len(records),
                "rejected": rejected,
                "rejection_reasons": rejection_reasons,
                "message": summary
            }

        # Perform transactional database operation
        try:
            with db.transaction() as conn:
                cur = conn.cursor()

                if import_policy == "Replace":
                    # Delete existing records in this primary table
                    if dataset_name == "animals":
                        cur.execute("UPDATE animals SET dam_id = NULL, sire_id = NULL")
                    cur.execute(f"DELETE FROM {dataset_name}")

                for rec in validated_records:
                    pk_val = rec.get(pk_col)
                    cur.execute(f"SELECT 1 FROM {dataset_name} WHERE {pk_col} = ?", (pk_val,))
                    exists = bool(cur.fetchone())

                    if exists:
                        if import_policy == "Skip duplicates":
                            skipped += 1
                            continue
                        elif import_policy == "Reject duplicates":
                            raise ValueError(f"Duplicate key '{pk_val}' found under Reject duplicates policy.")
                        elif import_policy in ("Update existing", "Append"):
                            # Update existing record
                            set_cols = [f"{k} = ?" for k in rec.keys() if k != pk_col]
                            if set_cols:
                                update_query = f"UPDATE {dataset_name} SET {', '.join(set_cols)} WHERE {pk_col} = ?"
                                cur.execute(update_query, [rec[k] for k in rec.keys() if k != pk_col] + [pk_val])
                                updated += 1
                            else:
                                skipped += 1
                    else:
                        # Insert fresh record
                        cols = list(rec.keys())
                        placeholders = ", ".join(["?"] * len(cols))
                        insert_query = f"INSERT INTO {dataset_name} ({', '.join(cols)}) VALUES ({placeholders})"
                        cur.execute(insert_query, list(rec.values()))
                        inserted += 1

                # Record import batch
                status = "COMPLETED"
                summary = f"Inserted: {inserted}, Updated: {updated}, Skipped: {skipped}, Rejected: {rejected}"
                cur.execute(
                    """
                    INSERT INTO import_batches (
                        import_batch_id, dataset_name, original_filename, import_datetime,
                        import_operation, records_received, records_inserted, records_updated,
                        records_skipped, records_rejected, import_status, validation_summary
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (import_batch_id, dataset_name, filename, now, import_policy, len(records), inserted, updated, skipped, rejected, status, summary)
                )

            # Audit log
            AuditManager.log_action(
                action_type="CSV_IMPORT",
                dataset_name=dataset_name,
                operation_id=import_batch_id,
                action_summary=f"Policy: {import_policy}, {summary}",
                affected_record_count=inserted + updated,
                result_status="SUCCESS"
            )

            return {
                "success": True,
                "batch_id": import_batch_id,
                "records_received": len(records),
                "inserted": inserted,
                "updated": updated,
                "skipped": skipped,
                "rejected": rejected,
                "rejection_reasons": rejection_reasons,
                "message": summary
            }

        except Exception as e:
            logger.error(f"Import transaction failed: {e}")
            AuditManager.log_action(
                action_type="CSV_IMPORT_FAILED",
                dataset_name=dataset_name,
                operation_id=import_batch_id,
                action_summary=f"Failed import: {str(e)}",
                affected_record_count=0,
                result_status="FAILED"
            )
            return {
                "success": False,
                "batch_id": import_batch_id,
                "records_received": len(records),
                "inserted": 0,
                "updated": 0,
                "skipped": 0,
                "rejected": len(records),
                "rejection_reasons": [str(e)],
                "message": f"Transaction rolled back due to error: {e}"
            }

    @staticmethod
    def sanitize_for_export(val: Any) -> Any:
        """Sanitizes text values against CSV Formula Injection (=, +, -, @)."""
        if isinstance(val, str) and len(val) > 0:
            if val.startswith(CSV_FORMULA_PREFIXES):
                return "'" + val
        return val
