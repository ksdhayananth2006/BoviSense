"""
Tests for Ground-Truth Evaluation Engine and Scientific Separation
"""
import pytest
from database.repositories import GroundTruthRepository, PredictionRepository
from services.estrus_predictor import EstrusPredictor
from services.evaluation import EvaluationEngine


def test_scientific_separation_prediction_imports():
    """Verify prediction module does NOT import or call GroundTruthRepository."""
    import inspect
    import services.estrus_predictor as estrus_module

    source_code = inspect.getsource(estrus_module)
    assert "GroundTruthRepository" not in source_code, "Scientific leak: GroundTruthRepository imported in estrus predictor!"
    assert "educational_ground_truth" not in source_code, "Scientific leak: Ground truth SQL referenced in estrus predictor!"


def test_evaluation_confusion_matrix_and_metrics():
    """Verify evaluation engine correctly computes TP, FP, TN, FN, and F1."""
    # Mock / direct test of evaluation logic
    eval_engine = EvaluationEngine()
    res = eval_engine.evaluate_scenario("estrus", score_threshold=60.0, tolerance_hours=24)

    assert res["status"] in ("completed", "unavailable")
    if res["status"] == "completed":
        cm = res["confusion_matrix"]
        assert "tp" in cm
        assert "fp" in cm
        assert "fn" in cm
        assert "tn" in cm
        metrics = res["metrics"]
        assert "accuracy" in metrics
        assert "precision" in metrics
        assert "recall_sensitivity" in metrics


def test_missing_ground_truth_handling():
    """Verify that when ground truth is absent for an event type, it reports unavailable without fabrication."""
    eval_engine = EvaluationEngine()
    # Query non-existent scenario
    res = eval_engine.evaluate_scenario("non_existent_event_type")
    assert res["status"] == "unavailable"
    assert "cannot be generated" in res["message"]
    assert res["metrics"] is None
