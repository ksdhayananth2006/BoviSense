"""
BOVISENSE Baseline Calculation Engine
Computes rolling individual animal baselines (mean, std, median, MAD)
with strict validity and data coverage thresholds.
"""
import datetime
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple

from config.thresholds import MIN_BASELINE_OBS_DAYS


class BaselineCalculator:
    """Calculates individual physiological and behavioral baselines."""

    @staticmethod
    def calculate_stats(values: List[float]) -> Dict[str, Optional[float]]:
        """Calculates parametric and robust non-parametric metrics."""
        clean = [float(v) for v in values if v is not None and not np.isnan(v)]
        if not clean:
            return {"mean": None, "std": None, "median": None, "mad": None, "count": 0}

        arr = np.array(clean)
        mean_val = float(np.mean(arr))
        std_val = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
        median_val = float(np.median(arr))
        mad_val = float(np.median(np.abs(arr - median_val)))

        return {
            "mean": round(mean_val, 2),
            "std": round(std_val, 2),
            "median": round(median_val, 2),
            "mad": round(mad_val, 2),
            "count": len(clean)
        }

    @staticmethod
    def compute_animal_baseline(
        observations: List[Dict[str, Any]],
        parameter: str,
        window_days: int = 14,
        target_timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Computes rolling baseline for a parameter over specified prior window_days.
        Requires at least MIN_BASELINE_OBS_DAYS distinct calendar dates with valid observations.
        """
        if not observations:
            return {
                "status": "insufficient_data",
                "reason": "No observations provided",
                "distinct_days": 0,
                "stats": None
            }

        df = pd.DataFrame(observations)
        if "quality_status" in df.columns:
            # Filter only valid or manually entered observations for baseline integrity
            df = df[df["quality_status"].isin(["valid", "manually_entered"])]

        if df.empty or parameter not in df.columns:
            return {
                "status": "insufficient_data",
                "reason": f"No valid observations for parameter '{parameter}'",
                "distinct_days": 0,
                "stats": None
            }

        # Timestamp filtering
        df["dt"] = pd.to_datetime(df["timestamp"])
        if target_timestamp:
            target_dt = pd.to_datetime(target_timestamp)
            start_dt = target_dt - pd.Timedelta(days=window_days)
            df = df[(df["dt"] < target_dt) & (df["dt"] >= start_dt)]

        df["date_str"] = df["dt"].dt.date
        valid_values = df[df[parameter].notnull() & (df[parameter] != "")]
        distinct_days = valid_values["date_str"].nunique()

        if distinct_days < MIN_BASELINE_OBS_DAYS:
            return {
                "status": "insufficient_data",
                "reason": f"Only {distinct_days} valid observation days found (minimum required: {MIN_BASELINE_OBS_DAYS})",
                "distinct_days": distinct_days,
                "stats": None
            }

        vals = valid_values[parameter].astype(float).tolist()
        stats = BaselineCalculator.calculate_stats(vals)

        return {
            "status": "valid",
            "parameter": parameter,
            "window_days": window_days,
            "distinct_days": distinct_days,
            "stats": stats
        }
