"""
BOVISENSE Temperature-Humidity Index (THI) Calculation Engine
Implements NRC (1971) standard formula and configurable bioclimatic stress bands.
"""
from typing import Dict, List, Optional, Tuple, Any

from config.thresholds import THI_BANDS


class THICalculator:
    """Calculates THI and classifies cattle thermal stress exposure."""

    @staticmethod
    def calculate_thi(temperature_c: float, relative_humidity_pct: float) -> float:
        """
        NRC (1971) Formula:
        THI = (1.8 * T + 32) - (0.55 - 0.0055 * RH) * (1.8 * T - 26)
        """
        t = float(temperature_c)
        rh = float(relative_humidity_pct)
        if rh < 0 or rh > 100:
            raise ValueError(f"Relative humidity must be between 0% and 100%, received {rh}")

        thi = (1.8 * t + 32.0) - (0.55 - 0.0055 * rh) * (1.8 * t - 26.0)
        return round(thi, 2)

    @staticmethod
    def classify_thi(thi_value: float, custom_bands: Optional[Dict[str, Dict[str, Any]]] = None) -> Tuple[str, str]:
        """
        Classifies THI value into stress category.
        Returns: (category_name, display_label)
        """
        bands = custom_bands or THI_BANDS
        val = float(thi_value)
        for cat, conf in bands.items():
            if conf["min"] <= val <= conf["max"]:
                return cat, conf.get("label", cat)
        return "Unknown", "Unclassified"

    @staticmethod
    def check_thi_discrepancy(imported_thi: Optional[float], calculated_thi: float, tolerance: float = 0.5) -> bool:
        """Flags whether imported THI differs meaningfully from formula calculation."""
        if imported_thi is None:
            return False
        return abs(float(imported_thi) - calculated_thi) > tolerance
