"""
BOVISENSE Reproductive Analytics and Breeding Management Service
Handles breeding timelines, cycle projections, gestation estimation, and service records.
"""
import datetime
import logging
from typing import Any, Dict, List, Optional, Tuple

from config.thresholds import REPRODUCTIVE_CONSTANTS
from database.repositories import ReproductiveRepository

logger = logging.getLogger("bovisense.reproduction")


class ReproductiveManager:
    """Manages estrous cycle calculations, gestation projections, and breeding history."""

    def __init__(self, repro_repo: Optional[ReproductiveRepository] = None):
        self.repro_repo = repro_repo or ReproductiveRepository()

    @staticmethod
    def calculate_return_to_estrus(
        service_or_estrus_date: str,
        cycle_length_days: int = REPRODUCTIVE_CONSTANTS["estrous_cycle_days"]
    ) -> Dict[str, Any]:
        """
        Calculates projected return-to-estrus window.
        Reference: 21-day average cycle (range 18 to 24 days).
        """
        dt = datetime.datetime.fromisoformat(service_or_estrus_date.replace("Z", "+00:00"))
        expected_date = dt + datetime.timedelta(days=cycle_length_days)
        window_start = dt + datetime.timedelta(days=REPRODUCTIVE_CONSTANTS["estrous_cycle_range"][0])
        window_end = dt + datetime.timedelta(days=REPRODUCTIVE_CONSTANTS["estrous_cycle_range"][1])

        return {
            "reference_date": service_or_estrus_date,
            "cycle_days_used": cycle_length_days,
            "expected_return_date": expected_date.date().isoformat(),
            "window_start": window_start.date().isoformat(),
            "window_end": window_end.date().isoformat(),
            "is_estimate": True
        }

    @staticmethod
    def estimate_calving_due_date(
        conception_or_ai_date: str,
        gestation_days: int = REPRODUCTIVE_CONSTANTS["gestation_days_typical"]
    ) -> Dict[str, Any]:
        """
        Estimates expected calving due date.
        Explicitly labeled as an educational projection.
        """
        dt = datetime.datetime.fromisoformat(conception_or_ai_date.replace("Z", "+00:00"))
        due_date = dt + datetime.timedelta(days=gestation_days)
        window_start = dt + datetime.timedelta(days=REPRODUCTIVE_CONSTANTS["gestation_days_range"][0])
        window_end = dt + datetime.timedelta(days=REPRODUCTIVE_CONSTANTS["gestation_days_range"][1])

        return {
            "assumed_conception_date": conception_or_ai_date,
            "gestation_days_used": gestation_days,
            "estimated_due_date": due_date.date().isoformat(),
            "due_window_start": window_start.date().isoformat(),
            "due_window_end": window_end.date().isoformat(),
            "disclaimer": "Projection based on 279-day average gestation; individual duration varies by breed and parity."
        }
