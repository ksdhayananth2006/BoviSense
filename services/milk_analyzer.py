"""
BOVISENSE Milk Production and Quality Analytics Service
Distinguishes milking session records from complete daily records without double-counting.
"""
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple

from database.repositories import MilkAndBCSRepository


class MilkAnalyzer:
    """Processes milking yields, lactation persistence, and milk quality metrics."""

    def __init__(self, milk_repo: Optional[MilkAndBCSRepository] = None):
        self.milk_repo = milk_repo or MilkAndBCSRepository()

    @staticmethod
    def aggregate_daily_yields(records: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Aggregates milk records into clean daily totals without double-counting.
        Session records ('session') have their morning/evening yields summed.
        Daily records ('daily_total') use total_yield_l directly.
        """
        if not records:
            return pd.DataFrame(columns=["date", "total_yield_l", "record_count", "avg_scc"])

        df = pd.DataFrame(records)
        df["dt"] = pd.to_datetime(df["record_datetime"])
        df["date"] = df["dt"].dt.date

        daily_rows = []
        for d, group in df.groupby("date"):
            # Check if there is a daily_total record
            daily_recs = group[group["record_type"] == "daily_total"]
            if not daily_recs.empty:
                tot_yield = float(daily_recs["total_yield_l"].iloc[0])
            else:
                # Sum session yields
                tot_yield = 0.0
                for _, r in group.iterrows():
                    y = r.get("total_yield_l")
                    if y is not None and not pd.isna(y):
                        tot_yield += float(y)
                    else:
                        m = float(r.get("morning_yield_l") or 0.0)
                        e = float(r.get("evening_yield_l") or 0.0)
                        tot_yield += (m + e)

            # Average SCC if present
            scc_vals = group["somatic_cell_count"].dropna().tolist()
            avg_scc = sum(scc_vals) / len(scc_vals) if scc_vals else None

            daily_rows.append({
                "date": str(d),
                "total_yield_l": round(tot_yield, 2),
                "record_count": len(group),
                "avg_scc": round(avg_scc, 1) if avg_scc is not None else None
            })

        res_df = pd.DataFrame(daily_rows).sort_values("date")
        return res_df
