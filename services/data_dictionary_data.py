"""
BOVISENSE Comprehensive Biological Data Dictionary
Provides complete educational metadata for all 13 primary datasets.
"""
from typing import Dict, List, Any

DATA_DICTIONARY: Dict[str, List[Dict[str, Any]]] = {
    "animals": [
        {
            "column": "animal_id", "type": "TEXT", "unit": "-", "required": "Yes",
            "permitted": "Alphanumeric string (e.g. COW-001)", "rule": "Must be unique primary key",
            "example": "COW-001", "description": "Unique farm identification tag for the animal.",
            "interpretation": "Biological subject identifier for longitudinal tracking."
        },
        {
            "column": "animal_name", "type": "TEXT", "unit": "-", "required": "No",
            "permitted": "Any valid name", "rule": "Optional textual identifier",
            "example": "Bella", "description": "Common herd name assigned to animal.",
            "interpretation": "Facilitates management communication."
        },
        {
            "column": "animal_type", "type": "TEXT", "unit": "-", "required": "Yes",
            "permitted": "cow, bull, calf, heifer, steer", "rule": "Strict categorical enum",
            "example": "cow", "description": "Classification category based on age, sex, and reproductive status.",
            "interpretation": "Determines physiological expectations and nutritional groupings."
        },
        {
            "column": "sex", "type": "TEXT", "unit": "-", "required": "Yes",
            "permitted": "F, M", "rule": "Binary biological sex indicator",
            "example": "F", "description": "Phenotypic/biological sex of the animal.",
            "interpretation": "Controls reproductive analytics and breeding eligibility."
        },
        {
            "column": "breed", "type": "TEXT", "unit": "-", "required": "Yes",
            "permitted": "Holstein, Jersey, Sahiwal, Gir, Crossbred, etc.", "rule": "Standard breed names",
            "example": "Holstein", "description": "Genetic lineage and breed classification.",
            "interpretation": "Dictates baseline metabolic rate, heat tolerance, and yield benchmarks."
        },
        {
            "column": "dob", "type": "TEXT", "unit": "YYYY-MM-DD", "required": "Yes",
            "permitted": "ISO 8601 calendar date", "rule": "Cannot be future date or earlier than dam DOB",
            "example": "2021-04-12", "description": "Verified date of birth.",
            "interpretation": "Determines chronological age, parity benchmarks, and maturation milestones."
        },
        {
            "column": "current_weight_kg", "type": "REAL", "unit": "kg", "required": "No",
            "permitted": "20.0 to 1200.0", "rule": "Positive real number",
            "example": "580.5", "description": "Latest recorded body weight.",
            "interpretation": "Indicator of metabolic frame and mature body reserve."
        },
        {
            "column": "reproductive_status", "type": "TEXT", "unit": "-", "required": "No",
            "permitted": "open, bred, pregnant, dry, lactating, not_eligible, unknown", "rule": "Standard status",
            "example": "open", "description": "Current physiological reproductive state.",
            "interpretation": "Guides artificial insemination eligibility and estrus expectation."
        }
    ],
    "sensor_observations": [
        {
            "column": "observation_id", "type": "TEXT", "unit": "-", "required": "Yes",
            "permitted": "Alphanumeric", "rule": "Primary key",
            "example": "OBS-001001", "description": "Unique sensor observation batch event.",
            "interpretation": "Granular longitudinal time-slice."
        },
        {
            "column": "animal_id", "type": "TEXT", "unit": "-", "required": "Yes",
            "permitted": "Valid animal_id", "rule": "Foreign key referencing animals table",
            "example": "COW-001", "description": "Monitored animal.",
            "interpretation": "Associates telemetry to individual animal baseline."
        },
        {
            "column": "timestamp", "type": "TEXT", "unit": "ISO 8601", "required": "Yes",
            "permitted": "YYYY-MM-DDTHH:MM:SS", "rule": "Chronological timestamp",
            "example": "2026-05-10T08:00:00", "description": "Start of sensor interval window.",
            "interpretation": "Time reference for circadian and seasonal pattern analysis."
        },
        {
            "column": "activity_count", "type": "REAL", "unit": "counts/interval", "required": "No",
            "permitted": ">= 0.0", "rule": "Non-negative real value",
            "example": "145.2", "description": "Tri-axial accelerometer raw or index activity score.",
            "interpretation": "Primary behavioural indicator for estrus restlessness and restlessness."
        },
        {
            "column": "rumination_time_min", "type": "REAL", "unit": "minutes", "required": "No",
            "permitted": "0.0 to interval length", "rule": "Must not exceed observation window",
            "example": "35.0", "description": "Total acoustic or accelerometer rumination duration.",
            "interpretation": "Sensitive early indicator of digestive health and systemic stress."
        },
        {
            "column": "body_temperature_c", "type": "REAL", "unit": "°C", "required": "No",
            "permitted": "34.0 to 45.0", "rule": "Physiological plausible boundary",
            "example": "38.6", "description": "Measured reticular, ear skin, or vaginal temperature.",
            "interpretation": "Thermoregulatory homeostasis marker for fever and heat stress screening."
        },
        {
            "column": "quality_status", "type": "TEXT", "unit": "-", "required": "Yes",
            "permitted": "valid, missing, invalid, suspect, estimated, manually_entered", "rule": "Quality enum",
            "example": "valid", "description": "Explicit data quality audit classification.",
            "interpretation": "Prevents faulty sensor telemetry from corrupting baseline calculations."
        }
    ],
    "environmental_observations": [
        {
            "column": "environment_id", "type": "TEXT", "unit": "-", "required": "Yes",
            "permitted": "Alphanumeric", "rule": "Primary key",
            "example": "ENV-001", "description": "Unique environmental log record.",
            "interpretation": "Microclimatic observation instance."
        },
        {
            "column": "temperature_c", "type": "REAL", "unit": "°C", "required": "Yes",
            "permitted": "-40.0 to 60.0", "rule": "Physical ambient temperature bounds",
            "example": "28.5", "description": "Dry bulb ambient barn temperature.",
            "interpretation": "Primary thermal stress driver."
        },
        {
            "column": "relative_humidity_pct", "type": "REAL", "unit": "%", "required": "Yes",
            "permitted": "0.0 to 100.0", "rule": "Physical percentage bounds",
            "example": "75.0", "description": "Atmospheric moisture percentage.",
            "interpretation": "Governs evaporative cooling capacity of cattle via respiration and sweating."
        },
        {
            "column": "thi_value", "type": "REAL", "unit": "Index units", "required": "No",
            "permitted": ">= 0.0", "rule": "Calculated via NRC (1971) formula",
            "example": "78.2", "description": "Temperature-Humidity Index composite score.",
            "interpretation": "Quantifies severity of bioclimatic heat stress."
        }
    ],
    "educational_ground_truth": [
        {
            "column": "truth_id", "type": "TEXT", "unit": "-", "required": "Yes",
            "permitted": "Alphanumeric", "rule": "Primary key",
            "example": "GT-001", "description": "Unique ground truth annotation record.",
            "interpretation": "Gold-standard reference label."
        },
        {
            "column": "event_type", "type": "TEXT", "unit": "-", "required": "Yes",
            "permitted": "estrus, heat_stress, fever_screening, respiratory_screening, mastitis_screening",
            "rule": "Controlled clinical event taxonomy",
            "example": "estrus", "description": "Target biological phenomenon being evaluated.",
            "interpretation": "Ground truth class label for confusion matrix formulation."
        },
        {
            "column": "label_value", "type": "TEXT", "unit": "-", "required": "Yes",
            "permitted": "positive, negative, unknown", "rule": "Ternary classification label",
            "example": "positive", "description": "Validated presence or absence of the biological state.",
            "interpretation": "Gold truth: unknown is never treated as negative."
        }
    ]
}
