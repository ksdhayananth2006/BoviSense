"""
BOVISENSE Formal Data Validation and Quality Control Service
Performs technical schema, physical range, and biological contextual validations.
"""
import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from config.settings import PRIMARY_DATASETS, QUALITY_STATUSES

DATASET_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "animals": {
        "primary_key": "animal_id",
        "required": ["animal_id", "animal_type", "sex", "breed", "dob"],
        "columns": [
            "animal_id", "animal_name", "animal_type", "sex", "breed", "dob",
            "acquisition_type", "acquisition_date", "dam_id", "sire_id",
            "birth_weight_kg", "current_weight_kg", "parity", "lactation_number",
            "reproductive_status", "health_status", "animal_status", "barn_id", "remarks"
        ],
        "types": {
            "birth_weight_kg": float, "current_weight_kg": float,
            "parity": int, "lactation_number": int
        },
        "enums": {
            "sex": ["F", "M", "FEMALE", "MALE"],
            "animal_type": ["cow", "bull", "calf", "heifer", "steer"],
            "animal_status": ["active", "sold", "culled", "deceased"]
        }
    },
    "sensor_observations": {
        "primary_key": "observation_id",
        "required": ["observation_id", "animal_id", "timestamp"],
        "columns": [
            "observation_id", "animal_id", "timestamp", "sensor_id",
            "observation_interval_minutes", "activity_count", "step_count",
            "standing_time_min", "lying_time_min", "rumination_time_min",
            "feeding_time_min", "mounts_performed", "mounts_received",
            "standing_to_be_mounted_count", "body_temperature_c", "temperature_method",
            "temperature_site", "respiratory_rate_breaths_min", "water_intake_l",
            "feed_intake_kg", "feed_measurement_basis", "data_source",
            "quality_status", "quality_notes"
        ],
        "types": {
            "observation_interval_minutes": int, "activity_count": float, "step_count": float,
            "standing_time_min": float, "lying_time_min": float, "rumination_time_min": float,
            "feeding_time_min": float, "mounts_performed": int, "mounts_received": int,
            "standing_to_be_mounted_count": int, "body_temperature_c": float,
            "respiratory_rate_breaths_min": float, "water_intake_l": float, "feed_intake_kg": float
        },
        "enums": {
            "quality_status": QUALITY_STATUSES
        }
    },
    "environmental_observations": {
        "primary_key": "environment_id",
        "required": ["environment_id", "timestamp", "temperature_c", "relative_humidity_pct"],
        "columns": [
            "environment_id", "barn_id", "timestamp", "temperature_c",
            "relative_humidity_pct", "wind_speed_ms", "solar_radiation_wm2",
            "thi_value", "thi_formula_version", "heat_stress_category",
            "data_source", "quality_status"
        ],
        "types": {
            "temperature_c": float, "relative_humidity_pct": float,
            "wind_speed_ms": float, "solar_radiation_wm2": float, "thi_value": float
        },
        "enums": {
            "quality_status": QUALITY_STATUSES
        }
    },
    "reproductive_events": {
        "primary_key": "event_id",
        "required": ["event_id", "animal_id", "event_datetime", "event_type"],
        "columns": [
            "event_id", "animal_id", "event_datetime", "event_type",
            "event_source", "observation_notes", "confirmation_status",
            "confirmed_by", "confirmation_datetime", "linked_prediction_id"
        ],
        "types": {},
        "enums": {}
    },
    "ai_records": {
        "primary_key": "ai_id",
        "required": ["ai_id", "animal_id", "ai_datetime"],
        "columns": [
            "ai_id", "animal_id", "event_id", "ai_datetime", "semen_bull_id",
            "semen_batch_id", "technician", "ai_attempt_number", "ai_type",
            "conception_method", "outcome_status", "remarks"
        ],
        "types": {"ai_attempt_number": int},
        "enums": {}
    },
    "pregnancy_records": {
        "primary_key": "pregnancy_id",
        "required": ["pregnancy_id", "animal_id", "examination_date", "examination_method", "pregnancy_status"],
        "columns": [
            "pregnancy_id", "animal_id", "ai_id", "examination_date",
            "examination_method", "pregnancy_status", "estimated_days_pregnant",
            "estimated_due_date", "conception_date", "conception_date_status",
            "veterinarian_id", "notes"
        ],
        "types": {"estimated_days_pregnant": int},
        "enums": {}
    },
    "calving_records": {
        "primary_key": "calving_id",
        "required": ["calving_id", "dam_id", "calving_datetime"],
        "columns": [
            "calving_id", "dam_id", "calving_datetime", "ai_id",
            "conception_method", "calving_type", "calf_count",
            "calving_outcome", "complications", "veterinarian_id", "remarks"
        ],
        "types": {"calf_count": int},
        "enums": {}
    },
    "health_observations": {
        "primary_key": "health_observation_id",
        "required": ["health_observation_id", "animal_id", "observation_datetime"],
        "columns": [
            "health_observation_id", "animal_id", "observation_datetime",
            "body_temperature_c", "temperature_method", "respiratory_rate_breaths_min",
            "feed_intake_status", "water_intake_status", "cough", "nasal_discharge",
            "ocular_discharge", "letargy", "udder_swelling", "abnormal_milk",
            "udder_pain", "manure_abnormality", "observed_by", "data_source", "notes"
        ],
        "types": {
            "body_temperature_c": float, "respiratory_rate_breaths_min": float,
            "cough": int, "nasal_discharge": int, "ocular_discharge": int,
            "letargy": int, "udder_swelling": int, "abnormal_milk": int, "udder_pain": int
        },
        "enums": {}
    },
    "health_alerts": {
        "primary_key": "alert_id",
        "required": ["alert_id", "animal_id", "alert_datetime", "alert_category", "priority"],
        "columns": [
            "alert_id", "animal_id", "alert_datetime", "alert_category",
            "priority", "alert_score", "triggering_parameters", "current_status",
            "veterinarian_notes", "resolution_datetime", "linked_health_event_id"
        ],
        "types": {"alert_score": float},
        "enums": {
            "priority": ["low", "medium", "high", "critical"],
            "current_status": ["active", "acknowledged", "resolved", "dismissed"]
        }
    },
    "milk_records": {
        "primary_key": "milk_record_id",
        "required": ["milk_record_id", "animal_id", "record_datetime", "milking_session", "record_type"],
        "columns": [
            "milk_record_id", "animal_id", "record_datetime", "milking_session",
            "record_type", "morning_yield_l", "evening_yield_l", "total_yield_l",
            "milk_conductivity", "somatic_cell_count", "milk_appearance",
            "data_source", "remarks"
        ],
        "types": {
            "morning_yield_l": float, "evening_yield_l": float, "total_yield_l": float,
            "milk_conductivity": float, "somatic_cell_count": float
        },
        "enums": {
            "record_type": ["session", "daily_total"]
        }
    },
    "bcs_records": {
        "primary_key": "bcs_record_id",
        "required": ["bcs_record_id", "animal_id", "assessment_date", "bcs_value"],
        "columns": [
            "bcs_record_id", "animal_id", "assessment_date", "bcs_value",
            "assessor", "assessment_method", "lactation_stage", "body_weight_kg", "remarks"
        ],
        "types": {"bcs_value": float, "body_weight_kg": float},
        "enums": {}
    },
    "calf_care_records": {
        "primary_key": "care_record_id",
        "required": ["care_record_id", "animal_id", "event_datetime", "care_type"],
        "columns": [
            "care_record_id", "animal_id", "event_datetime", "care_type",
            "quantity", "quantity_unit", "colostrum_brix_pct", "vaccination_name",
            "medication_name", "administered_by", "notes"
        ],
        "types": {"quantity": float, "colostrum_brix_pct": float},
        "enums": {}
    },
    "educational_ground_truth": {
        "primary_key": "truth_id",
        "required": ["truth_id", "animal_id", "event_type", "period_start", "period_end", "label_value"],
        "columns": [
            "truth_id", "animal_id", "event_type", "period_start", "period_end",
            "label_value", "label_source", "confirmation_method", "annotator",
            "annotation_datetime", "label_confidence", "scenario_id", "notes", "revision_status"
        ],
        "types": {"label_confidence": float},
        "enums": {
            "label_value": ["positive", "negative", "unknown"],
            "event_type": [
                "estrus", "heat_stress", "fever_screening",
                "respiratory_screening", "mastitis_screening", "other_health_event"
            ]
        }
    }
}


class DataValidator:
    """Validates records and files against strict technical and biological rules."""

    @staticmethod
    def get_schema(dataset_name: str) -> Optional[Dict[str, Any]]:
        return DATASET_SCHEMAS.get(dataset_name)

    @staticmethod
    def validate_record(dataset_name: str, record: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """
        Validates a single record dictionary.
        Returns: (is_valid, list_of_errors, list_of_warnings_or_suspect_reasons)
        """
        schema = DATASET_SCHEMAS.get(dataset_name)
        if not schema:
            return False, [f"Unknown dataset: {dataset_name}"], []

        errors: List[str] = []
        warnings: List[str] = []

        # 1. Required field checks
        for req in schema["required"]:
            val = record.get(req)
            if val is None or str(val).strip() == "" or str(val).lower() == "nan":
                errors.append(f"Missing required field: '{req}'")

        # 2. Type conversions and Range checks
        for field, expected_type in schema.get("types", {}).items():
            val = record.get(field)
            if val is not None and str(val).strip() != "" and str(val).lower() != "nan":
                try:
                    expected_type(val)
                except (ValueError, TypeError):
                    errors.append(f"Field '{field}' with value '{val}' cannot be converted to {expected_type.__name__}")

        # 3. Enum checks
        for field, valid_values in schema.get("enums", {}).items():
            val = record.get(field)
            if val is not None and str(val).strip() != "" and str(val).lower() != "nan":
                if str(val) not in valid_values:
                    errors.append(f"Field '{field}' has invalid categorical value '{val}'. Allowed: {valid_values}")

        # 4. Specific Biological Validations
        if dataset_name == "animals":
            animal_id = str(record.get("animal_id", "")).strip()
            dam_id = str(record.get("dam_id", "")).strip()
            sire_id = str(record.get("sire_id", "")).strip()
            if animal_id and dam_id and animal_id == dam_id:
                errors.append("Biological violation: Animal cannot be its own dam.")
            if animal_id and sire_id and animal_id == sire_id:
                errors.append("Biological violation: Animal cannot be its own sire.")
            
            # Weight checks
            b_wt = record.get("birth_weight_kg")
            if b_wt is not None and str(b_wt).strip() != "" and str(b_wt).lower() != "nan":
                try:
                    wt = float(b_wt)
                    if wt <= 0:
                        errors.append("Birth weight must be strictly positive.")
                    elif wt > 100:
                        warnings.append("Birth weight > 100 kg is biologically suspect.")
                except ValueError:
                    pass

        elif dataset_name == "sensor_observations":
            temp = record.get("body_temperature_c")
            if temp is not None and str(temp).strip() != "" and str(temp).lower() != "nan":
                try:
                    t = float(temp)
                    if t < 34.0 or t > 45.0:
                        errors.append(f"Temperature {t}°C is outside plausible physiological survival limits (34-45°C).")
                    elif t < 37.0 or t > 41.5:
                        warnings.append(f"Temperature {t}°C is unusual; flagged as suspect.")
                except ValueError:
                    pass

        elif dataset_name == "environmental_observations":
            rh = record.get("relative_humidity_pct")
            if rh is not None and str(rh).strip() != "" and str(rh).lower() != "nan":
                try:
                    r_val = float(rh)
                    if r_val < 0.0 or r_val > 100.0:
                        errors.append(f"Relative humidity must be within 0% to 100%, found {r_val}%.")
                except ValueError:
                    pass

        elif dataset_name == "bcs_records":
            bcs = record.get("bcs_value")
            if bcs is not None and str(bcs).strip() != "" and str(bcs).lower() != "nan":
                try:
                    b_val = float(bcs)
                    if b_val < 1.0 or b_val > 5.0:
                        errors.append(f"BCS value must be strictly between 1.0 and 5.0 on the Ferguson scale, found {b_val}.")
                except ValueError:
                    pass

        elif dataset_name == "educational_ground_truth":
            start = str(record.get("period_start", "")).strip()
            end = str(record.get("period_end", "")).strip()
            if start and end and start > end:
                errors.append(f"Period start ({start}) must not be later than period end ({end}).")

        is_valid = len(errors) == 0
        return is_valid, errors, warnings
