"""
BOVISENSE Rule-Based Estrus Indication and Prediction Engine
Strictly separated from ground-truth data access to eliminate data leakage.
"""
import datetime
import json
import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from config.thresholds import (
    DEFAULT_ESTRUS_WEIGHTS,
    ESTRUS_SCORE_BANDS,
    MIN_EVIDENCE_COVERAGE,
)
from database.repositories import AnimalRepository, PredictionRepository, SensorRepository
from services.baseline_calculator import BaselineCalculator
from services.thi_calculator import THICalculator

logger = logging.getLogger("bovisense.estrus")


class EstrusPredictor:
    """
    Computes rule-based estrus indications using baseline deviations and weights.
    DO NOT IMPORT OR CALL GROUND TRUTH IN THIS MODULE.
    """

    def __init__(
        self,
        sensor_repo: Optional[SensorRepository] = None,
        prediction_repo: Optional[PredictionRepository] = None,
        weights: Optional[Dict[str, float]] = None
    ):
        self.sensor_repo = sensor_repo or SensorRepository()
        self.prediction_repo = prediction_repo or PredictionRepository()
        self.weights = weights or DEFAULT_ESTRUS_WEIGHTS

    def evaluate_observation(
        self,
        current_obs: Dict[str, Any],
        historical_obs: List[Dict[str, Any]],
        thi_context: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Evaluates a single observation against the animal's individual baseline.
        Returns detailed scoring breakdown, evidence coverage, and interpretation category.
        """
        animal_id = current_obs.get("animal_id")
        obs_time = current_obs.get("timestamp")

        # 1. Calculate Baselines for relevant metrics
        act_baseline = BaselineCalculator.compute_animal_baseline(historical_obs, "activity_count", 14, obs_time)
        rum_baseline = BaselineCalculator.compute_animal_baseline(historical_obs, "rumination_time_min", 14, obs_time)
        std_baseline = BaselineCalculator.compute_animal_baseline(historical_obs, "standing_time_min", 14, obs_time)
        ly_baseline = BaselineCalculator.compute_animal_baseline(historical_obs, "lying_time_min", 14, obs_time)
        temp_baseline = BaselineCalculator.compute_animal_baseline(historical_obs, "body_temperature_c", 14, obs_time)

        contributions: Dict[str, float] = {}
        available_weights: float = 0.0
        contributing_params: Dict[str, Any] = {}

        # A. Activity Increase (Weight: 25%)
        w_act = self.weights.get("activity_increase", 0.25)
        act_val = current_obs.get("activity_count")
        if act_val is not None and act_baseline["status"] == "valid":
            b_mean = act_baseline["stats"]["mean"]
            b_std = max(act_baseline["stats"]["std"] or 1.0, 1.0)
            dev = (float(act_val) - b_mean) / b_std
            # Map z-score 0 to +3 to score 0 to 100
            score_act = float(np.clip(dev * 33.33, 0.0, 100.0))
            contributions["activity_increase"] = score_act * w_act
            available_weights += w_act
            contributing_params["activity_increase"] = {"val": act_val, "z_score": round(dev, 2), "score": round(score_act, 1)}

        # B. Standing Time Increase (Weight: 15%)
        w_std = self.weights.get("standing_time", 0.15)
        std_val = current_obs.get("standing_time_min")
        if std_val is not None and std_baseline["status"] == "valid":
            b_mean = std_baseline["stats"]["mean"]
            b_std = max(std_baseline["stats"]["std"] or 1.0, 1.0)
            dev = (float(std_val) - b_mean) / b_std
            score_std = float(np.clip(dev * 33.33, 0.0, 100.0))
            contributions["standing_time"] = score_std * w_std
            available_weights += w_std
            contributing_params["standing_time"] = {"val": std_val, "z_score": round(dev, 2), "score": round(score_std, 1)}

        # C. Standing to be Mounted (Count) (Weight: 15%)
        w_stbm = self.weights.get("standing_to_be_mounted", 0.15)
        stbm_val = current_obs.get("standing_to_be_mounted_count")
        if stbm_val is not None:
            # Sighting of standing to be mounted is high specificity (1 mount = 60, >=2 = 100)
            cnt = int(stbm_val)
            score_stbm = 100.0 if cnt >= 2 else (60.0 if cnt == 1 else 0.0)
            contributions["standing_to_be_mounted"] = score_stbm * w_stbm
            available_weights += w_stbm
            contributing_params["standing_to_be_mounted"] = {"count": cnt, "score": score_stbm}

        # D. Mounting Behaviour (Weight: 15%)
        w_mount = self.weights.get("mounting_behavior", 0.15)
        mounts_p = current_obs.get("mounts_performed") or 0
        mounts_r = current_obs.get("mounts_received") or 0
        tot_mounts = int(mounts_p) + int(mounts_r)
        if current_obs.get("mounts_performed") is not None or current_obs.get("mounts_received") is not None:
            score_mount = 100.0 if tot_mounts >= 3 else (50.0 if tot_mounts >= 1 else 0.0)
            contributions["mounting_behavior"] = score_mount * w_mount
            available_weights += w_mount
            contributing_params["mounting_behavior"] = {"total_mounts": tot_mounts, "score": score_mount}

        # E. Rumination Decrease (Weight: 15%)
        w_rum = self.weights.get("rumination_decrease", 0.15)
        rum_val = current_obs.get("rumination_time_min")
        if rum_val is not None and rum_baseline["status"] == "valid":
            b_mean = rum_baseline["stats"]["mean"]
            b_std = max(rum_baseline["stats"]["std"] or 1.0, 1.0)
            # Estrus typically shows a physiological decrease in rumination
            dev_drop = (b_mean - float(rum_val)) / b_std
            score_rum = float(np.clip(dev_drop * 33.33, 0.0, 100.0))
            contributions["rumination_decrease"] = score_rum * w_rum
            available_weights += w_rum
            contributing_params["rumination_decrease"] = {"val": rum_val, "drop_z": round(dev_drop, 2), "score": round(score_rum, 1)}

        # F. Lying Time Decrease (Weight: 5%)
        w_ly = self.weights.get("lying_time", 0.05)
        ly_val = current_obs.get("lying_time_min")
        if ly_val is not None and ly_baseline["status"] == "valid":
            b_mean = ly_baseline["stats"]["mean"]
            b_std = max(ly_baseline["stats"]["std"] or 1.0, 1.0)
            dev_ly = (b_mean - float(ly_val)) / b_std
            score_ly = float(np.clip(dev_ly * 33.33, 0.0, 100.0))
            contributions["lying_time"] = score_ly * w_ly
            available_weights += w_ly
            contributing_params["lying_time"] = {"val": ly_val, "drop_z": round(dev_ly, 2), "score": round(score_ly, 1)}

        # G. Temperature Change (Weight: 5%)
        w_tmp = self.weights.get("temperature_change", 0.05)
        tmp_val = current_obs.get("body_temperature_c")
        if tmp_val is not None and temp_baseline["status"] == "valid":
            b_mean = temp_baseline["stats"]["mean"]
            dev_t = abs(float(tmp_val) - b_mean)
            # Slight transient rise (0.3 to 0.8 °C) around estrus
            score_t = 100.0 if 0.3 <= dev_t <= 1.0 else (50.0 if dev_t > 0.1 else 0.0)
            contributions["temperature_change"] = score_t * w_tmp
            available_weights += w_tmp
            contributing_params["temperature_change"] = {"val": tmp_val, "abs_diff": round(dev_t, 2), "score": score_t}

        # 2. Evidence Coverage
        total_possible_weight = sum(self.weights.values())
        coverage = round(available_weights / total_possible_weight, 2) if total_possible_weight > 0 else 0.0

        if coverage < MIN_EVIDENCE_COVERAGE:
            return {
                "animal_id": animal_id,
                "timestamp": obs_time,
                "status": "insufficient_data",
                "score": None,
                "confidence_category": "Insufficient Data",
                "coverage": coverage,
                "message": f"Coverage {int(coverage*100)}% is below minimum requirement ({int(MIN_EVIDENCE_COVERAGE*100)}%).",
                "contributing_parameters": contributing_params
            }

        # 3. Normalized Score (scaled to available evidence weight)
        raw_weighted_sum = sum(contributions.values())
        final_score = round(raw_weighted_sum / available_weights, 1)

        # 4. Map to Configurable Category
        category = "Low"
        label = "Low Indication"
        action = "Routine Monitoring"
        for band_name, conf in ESTRUS_SCORE_BANDS.items():
            if conf["min"] <= final_score <= conf["max"]:
                category = band_name
                label = conf["label"]
                action = conf["action"]
                break

        # 5. Contextual THI Check
        thi_note = None
        if thi_context is not None:
            thi_cat, thi_label = THICalculator.classify_thi(thi_context)
            if thi_context >= 72.0:
                thi_note = f"Thermal stress ({thi_label}, THI={thi_context}) may independently alter activity/rumination patterns."

        return {
            "animal_id": animal_id,
            "timestamp": obs_time,
            "status": "calculated",
            "score": final_score,
            "confidence_category": label,
            "category_key": category,
            "action_recommendation": action,
            "coverage": coverage,
            "contributions": contributions,
            "contributing_parameters": contributing_params,
            "thi_context": thi_context,
            "thi_note": thi_note
        }

    def predict_and_store(
        self,
        current_obs: Dict[str, Any],
        historical_obs: List[Dict[str, Any]],
        thi_context: Optional[float] = None
    ) -> Dict[str, Any]:
        """Runs evaluation and persists prediction record."""
        res = self.evaluate_observation(current_obs, historical_obs, thi_context)
        if res["status"] == "calculated":
            pred_id = f"prd_{uuid.uuid4().hex[:12]}"
            data = {
                "prediction_id": pred_id,
                "animal_id": res["animal_id"],
                "prediction_datetime": res["timestamp"],
                "prediction_type": "estrus_indication",
                "prediction_score": res["score"],
                "contributing_parameters": json.dumps(res["contributing_parameters"]),
                "baseline_reference": "individual_14d_rolling",
                "data_coverage": res["coverage"],
                "confidence_category": res["confidence_category"],
                "algorithm_version": "2.0-RULE",
                "threshold_configuration": json.dumps(self.weights),
                "review_status": "pending_review",
                "notes": res.get("thi_note") or ""
            }
            self.prediction_repo.insert_prediction(data)
            res["prediction_id"] = pred_id
        return res
