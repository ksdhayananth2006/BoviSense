"""
BOVISENSE Newborn Calf and Growth Monitoring Service
Calculates Average Daily Gain (ADG) and evaluates early colostrum nutrition.
"""
import datetime
from typing import Any, Dict, List, Optional, Tuple

from database.db_manager import db


class CalfMonitor:
    """Manages calf growth rates and neonatal care standards."""

    @staticmethod
    def calculate_adg(
        start_weight_kg: float,
        end_weight_kg: float,
        days_between: int
    ) -> Optional[float]:
        """
        Calculates Average Daily Gain (ADG) in kg/day.
        ADG = (Weight2 - Weight1) / days_between
        """
        if days_between <= 0 or start_weight_kg <= 0 or end_weight_kg <= 0:
            return None
        return round((end_weight_kg - start_weight_kg) / float(days_between), 3)

    @staticmethod
    def evaluate_colostrum_brix(brix_percentage: float) -> Dict[str, str]:
        """
        Evaluates colostrum immunoglobulin quality via optical/digital Brix refractometry.
        Reference: Brix >= 22% indicates >= 50 g/L IgG (good quality).
        """
        val = float(brix_percentage)
        if val >= 22.0:
            return {"status": "Good", "quality": "High Quality Colostrum (IgG >= 50 g/L)", "action": "Suitable for initial feeding"}
        elif val >= 18.0:
            return {"status": "Borderline", "quality": "Moderate Quality Colostrum", "action": "Use for secondary feeding or supplement"}
        else:
            return {"status": "Poor", "quality": "Low Quality Colostrum (Risk of FPT)", "action": "Do not use as primary first colostrum"}
