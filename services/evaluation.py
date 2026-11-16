"""
BOVISENSE Independent Ground-Truth Evaluation Engine
Compares algorithm predictions against independently stored ground-truth annotations.
Strict separation: never modifies prediction records or injects ground truth into predictions.
"""
import datetime
import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from database.repositories import GroundTruthRepository, PredictionRepository

logger = logging.getLogger("bovisense.evaluation")


class EvaluationEngine:
    """Computes academic validation metrics and confusion matrices."""

    def __init__(
        self,
        pred_repo: Optional[PredictionRepository] = None,
        gt_repo: Optional[GroundTruthRepository] = None
    ):
        self.pred_repo = pred_repo or PredictionRepository()
        self.gt_repo = gt_repo or GroundTruthRepository()

    def evaluate_scenario(
        self,
        event_type: str = "estrus",
        score_threshold: float = 60.0,
        tolerance_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Matches predictions of event_type with independent ground-truth labels.
        Matches by animal_id and temporal proximity within tolerance_hours.
        """
        # Fetch ground truth labels
        labels = self.gt_repo.get_all(event_type=event_type)
        if not labels:
            return {
                "status": "unavailable",
                "message": f"Ground-truth dataset is empty or has no annotations for '{event_type}'. Evaluation metrics cannot be generated.",
                "event_type": event_type,
                "metrics": None
            }

        # Fetch predictions
        # Map event_type to prediction_type
        pred_type_map = {
            "estrus": "estrus_indication",
            "heat_stress": "heat_stress",
            "fever_screening": "fever_screening",
            "respiratory_screening": "respiratory_screening",
            "mastitis_screening": "mastitis_screening"
        }
        target_pred_type = pred_type_map.get(event_type, event_type)
        predictions = self.pred_repo.get_predictions(pred_type=target_pred_type)

        # Count positive and negative labels
        valid_labels = [l for l in labels if l["label_value"] in ("positive", "negative")]
        unknown_labels = [l for l in labels if l["label_value"] == "unknown"]

        tp = 0
        fp = 0
        fn = 0
        tn = 0
        matched_gt_ids = set()

        # For each valid ground truth label, check corresponding prediction
        for gt in valid_labels:
            a_id = gt["animal_id"]
            gt_start = datetime.datetime.fromisoformat(gt["period_start"].replace("Z", "+00:00"))
            gt_end = datetime.datetime.fromisoformat(gt["period_end"].replace("Z", "+00:00"))
            is_positive_gt = (gt["label_value"] == "positive")

            # Look for animal predictions around this period (+/- tolerance_hours)
            matching_preds = []
            for p in predictions:
                if p["animal_id"] == a_id:
                    p_dt = datetime.datetime.fromisoformat(p["prediction_datetime"].replace("Z", "+00:00"))
                    if (gt_start - datetime.timedelta(hours=tolerance_hours)) <= p_dt <= (gt_end + datetime.timedelta(hours=tolerance_hours)):
                        matching_preds.append(p)

            # Max score in window
            max_score = max([float(p["prediction_score"]) for p in matching_preds]) if matching_preds else 0.0
            predicted_positive = (max_score >= score_threshold)

            matched_gt_ids.add(gt["truth_id"])

            if is_positive_gt:
                if predicted_positive:
                    tp += 1
                else:
                    fn += 1
            else:  # ground truth negative
                if predicted_positive:
                    fp += 1
                else:
                    tn += 1

        total_cases = tp + tn + fp + fn
        if total_cases == 0:
            return {
                "status": "unavailable",
                "message": "No matching observation windows found between ground truth and algorithm predictions.",
                "event_type": event_type,
                "metrics": None
            }

        accuracy = round((tp + tn) / total_cases, 3) if total_cases > 0 else None
        precision = round(tp / (tp + fp), 3) if (tp + fp) > 0 else None
        recall = round(tp / (tp + fn), 3) if (tp + fn) > 0 else None
        specificity = round(tn / (tn + fp), 3) if (tn + fp) > 0 else None
        fpr = round(fp / (fp + tn), 3) if (fp + tn) > 0 else None
        
        if precision is not None and recall is not None and (precision + recall) > 0:
            f1 = round(2 * (precision * recall) / (precision + recall), 3)
        else:
            f1 = None

        return {
            "status": "completed",
            "event_type": event_type,
            "threshold_used": score_threshold,
            "tolerance_hours": tolerance_hours,
            "total_labels": len(labels),
            "evaluated_cases": total_cases,
            "unknown_labels_excluded": len(unknown_labels),
            "confusion_matrix": {
                "tp": tp, "fp": fp, "fn": fn, "tn": tn
            },
            "metrics": {
                "accuracy": accuracy,
                "precision": precision,
                "recall_sensitivity": recall,
                "specificity": specificity,
                "f1_score": f1,
                "false_positive_rate": fpr
            },
            "scientific_note": "Educational evaluation based on current ground-truth dataset. Missing/unknown labels are not treated as negative."
        }
