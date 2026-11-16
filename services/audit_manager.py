"""
BOVISENSE Audit and Operation Logging Service
"""
import datetime
import uuid
from typing import Optional

from database.db_manager import db


class AuditManager:
    """Logs administrative and data management actions for traceability."""

    @staticmethod
    def log_action(
        action_type: str,
        dataset_name: Optional[str] = None,
        record_id: Optional[str] = None,
        operation_id: Optional[str] = None,
        action_summary: Optional[str] = None,
        affected_record_count: int = 1,
        result_status: str = "SUCCESS"
    ) -> str:
        audit_id = f"aud_{uuid.uuid4().hex[:12]}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        db.execute(
            """
            INSERT INTO audit_logs (
                audit_id, timestamp, action_type, dataset_name, record_id,
                operation_id, action_summary, affected_record_count, result_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                audit_id, now, action_type, dataset_name, record_id,
                operation_id or str(uuid.uuid4()), action_summary,
                affected_record_count, result_status
            )
        )
        return audit_id

    @staticmethod
    def get_recent_logs(limit: int = 100) -> list:
        return db.fetchall("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT ?", (limit,))
