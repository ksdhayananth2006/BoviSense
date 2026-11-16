"""
BOVISENSE Synthetic Data Generator
Generates realistic biological scenarios, sensor observations, and independent ground-truth labels
for academic testing and system demonstration.
"""
import csv
import datetime
import math
import random
from pathlib import Path
from typing import Any, Dict, List, Tuple

from config.settings import SAMPLE_DATA_DIR


class SyntheticDataGenerator:
    """Produces biologically plausible synthetic datasets for all 13 primary datasets."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)
        self.sample_dir = SAMPLE_DATA_DIR
        self.sample_dir.mkdir(parents=True, exist_ok=True)

    def generate_all(self, days: int = 90, cow_count: int = 40, bull_count: int = 4, calf_count: int = 12) -> Dict[str, str]:
        """Generates all 13 primary sample CSVs in data/sample/."""
        start_date = datetime.date(2026, 1, 1)

        # 1. Animals
        animals = []
        # 40 Cows
        for i in range(1, cow_count + 1):
            cid = f"COW-{i:03d}"
            parity = random.choice([1, 2, 3, 4])
            lact_num = parity
            repro_stat = random.choice(["lactating", "lactating", "pregnant", "open", "dry"])
            dob = start_date - datetime.timedelta(days=int(365 * (parity + 2) + random.randint(0, 100)))
            animals.append({
                "animal_id": cid,
                "animal_name": f"Cow_{i}",
                "animal_type": "cow",
                "sex": "F",
                "breed": random.choice(["Holstein-Friesian", "Jersey", "Gir Cross"]),
                "dob": dob.isoformat(),
                "acquisition_type": "born_on_farm",
                "acquisition_date": dob.isoformat(),
                "dam_id": None,
                "sire_id": None,
                "birth_weight_kg": round(random.uniform(36.0, 42.0), 1),
                "current_weight_kg": round(random.uniform(520.0, 680.0), 1),
                "parity": parity,
                "lactation_number": lact_num,
                "reproductive_status": repro_stat,
                "health_status": "healthy",
                "animal_status": "active",
                "barn_id": "BARN-A" if repro_stat == "lactating" else "BARN-B",
                "remarks": "Synthetic dairy cow"
            })

        # 4 Bulls
        for i in range(1, bull_count + 1):
            bid = f"BULL-{i:03d}"
            dob = start_date - datetime.timedelta(days=int(365 * 4 + random.randint(0, 100)))
            animals.append({
                "animal_id": bid,
                "animal_name": f"Sire_{i}",
                "animal_type": "bull",
                "sex": "M",
                "breed": "Holstein-Friesian",
                "dob": dob.isoformat(),
                "acquisition_type": "purchased",
                "acquisition_date": (dob + datetime.timedelta(days=365)).isoformat(),
                "dam_id": None,
                "sire_id": None,
                "birth_weight_kg": 42.0,
                "current_weight_kg": round(random.uniform(850.0, 1050.0), 1),
                "parity": 0,
                "lactation_number": 0,
                "reproductive_status": "not_eligible",
                "health_status": "healthy",
                "animal_status": "active",
                "barn_id": "BARN-D",
                "remarks": "Synthetic breeding bull"
            })

        # 12 Calves
        for i in range(1, calf_count + 1):
            calf_id = f"CALF-{i:03d}"
            dam = f"COW-{i:03d}"
            sire = "BULL-001"
            dob = start_date + datetime.timedelta(days=int(random.randint(10, 60)))
            sex = random.choice(["F", "M"])
            b_wt = round(random.uniform(34.0, 44.0), 1)
            days_old = max((datetime.date(2026, 4, 1) - dob).days, 1)
            curr_wt = round(b_wt + (days_old * random.uniform(0.65, 0.85)), 1)
            animals.append({
                "animal_id": calf_id,
                "animal_name": f"Calf_{i}",
                "animal_type": "calf",
                "sex": sex,
                "breed": "Holstein-Friesian",
                "dob": dob.isoformat(),
                "acquisition_type": "born_on_farm",
                "acquisition_date": dob.isoformat(),
                "dam_id": dam,
                "sire_id": sire,
                "birth_weight_kg": b_wt,
                "current_weight_kg": curr_wt,
                "parity": 0,
                "lactation_number": 0,
                "reproductive_status": "not_eligible",
                "health_status": "healthy",
                "animal_status": "active",
                "barn_id": "BARN-C",
                "remarks": "Synthetic replacement stock"
            })

        self._write_csv("animals.csv", animals)

        # 2. Environmental Observations (Daily 4 readings for 90 days across Barn A & B)
        env_obs = []
        env_id_counter = 1
        for day in range(days):
            curr_dt = start_date + datetime.timedelta(days=day)
            # Simulate seasonal thermal curve (cooler early, heat spike mid-cycle)
            seasonal_temp = 22.0 + 12.0 * math.sin((day / 90.0) * math.pi)
            for hour in [6, 12, 16, 22]:
                dt_str = f"{curr_dt.isoformat()}T{hour:02d}:00:00"
                for barn in ["BARN-A", "BARN-B"]:
                    temp_c = round(seasonal_temp + random.uniform(-2.5, 3.5), 1)
                    rh_pct = round(min(max(60.0 + random.uniform(-15.0, 25.0), 20.0), 95.0), 1)
                    thi = round((1.8 * temp_c + 32.0) - (0.55 - 0.0055 * rh_pct) * (1.8 * temp_c - 26.0), 2)
                    category = "Low" if thi < 68 else ("Mild" if thi < 72 else ("Moderate" if thi < 79 else ("Severe" if thi < 84 else "Extreme")))
                    env_obs.append({
                        "environment_id": f"ENV-{env_id_counter:05d}",
                        "barn_id": barn,
                        "timestamp": dt_str,
                        "temperature_c": temp_c,
                        "relative_humidity_pct": rh_pct,
                        "wind_speed_ms": round(random.uniform(0.5, 3.5), 1),
                        "solar_radiation_wm2": round(random.uniform(100.0, 650.0), 1) if hour in [12, 16] else 0.0,
                        "thi_value": thi,
                        "thi_formula_version": "1.0",
                        "heat_stress_category": category,
                        "data_source": "barn_sensor_station",
                        "quality_status": "valid"
                    })
                    env_id_counter += 1
        self._write_csv("environmental_observations.csv", env_obs)

        # 3. Sensor Observations & Independent Ground Truth
        # Simulate selected cows (e.g. COW-001 through COW-010) with detailed 2-hour intervals
        sensor_obs = []
        ground_truth = []
        repro_events = []
        ai_records = []
        health_obs = []
        health_alerts = []
        milk_records = []
        bcs_records = []

        obs_id_cnt = 1
        gt_id_cnt = 1
        repro_id_cnt = 1
        ai_id_cnt = 1
        alert_id_cnt = 1
        milk_id_cnt = 1
        bcs_id_cnt = 1

        # Preset estrus events for COW-001 at Day 21 and Day 42
        estrus_schedule = {
            "COW-001": [21, 42],
            "COW-002": [15, 36],
            "COW-003": [28],
            "COW-004": [50]
        }
        # Preset fever event for COW-005 at Day 30
        fever_schedule = {"COW-005": 30}
        # Preset mastitis event for COW-006 at Day 45
        mastitis_schedule = {"COW-006": 45}

        for c_idx in range(1, 11):
            cow_id = f"COW-{c_idx:03d}"
            base_act = random.uniform(80.0, 110.0)
            base_rum = random.uniform(420.0, 480.0)
            base_temp = 38.5

            for day in range(days):
                curr_dt = start_date + datetime.timedelta(days=day)
                is_estrus_day = (day in estrus_schedule.get(cow_id, []))
                is_fever_day = (day == fever_schedule.get(cow_id, -1))
                is_mastitis_day = (day == mastitis_schedule.get(cow_id, -1))

                # Ground Truth labeling (Independent generation)
                if is_estrus_day:
                    gt_start = f"{curr_dt.isoformat()}T00:00:00"
                    gt_end = f"{curr_dt.isoformat()}T23:59:59"
                    ground_truth.append({
                        "truth_id": f"GT-{gt_id_cnt:05d}",
                        "animal_id": cow_id,
                        "event_type": "estrus",
                        "period_start": gt_start,
                        "period_end": gt_end,
                        "label_value": "positive",
                        "label_source": "progesterone_p4_elisa_assay",
                        "confirmation_method": "serum_progesterone_drop_and_standing_mount",
                        "annotator": "Senior Reproduction Specialist",
                        "annotation_datetime": f"{curr_dt.isoformat()}T18:00:00",
                        "label_confidence": 0.98,
                        "scenario_id": f"estrus_cycle_d{day}",
                        "notes": "Verified physiological estrus via ultrasound and P4 assay.",
                        "revision_status": "current"
                    })
                    gt_id_cnt += 1

                if is_fever_day:
                    ground_truth.append({
                        "truth_id": f"GT-{gt_id_cnt:05d}",
                        "animal_id": cow_id,
                        "event_type": "fever_screening",
                        "period_start": f"{curr_dt.isoformat()}T08:00:00",
                        "period_end": f"{curr_dt.isoformat()}T20:00:00",
                        "label_value": "positive",
                        "label_source": "veterinary_rectal_thermometer",
                        "confirmation_method": "clinical_examination",
                        "annotator": "Attending Veterinarian",
                        "annotation_datetime": f"{curr_dt.isoformat()}T12:00:00",
                        "label_confidence": 0.95,
                        "scenario_id": "acute_pyrexia",
                        "notes": "Rectal temperature measured 40.2 C.",
                        "revision_status": "current"
                    })
                    gt_id_cnt += 1

                # Generate sensor readings at 4-hour intervals
                for hour in [0, 4, 8, 12, 16, 20]:
                    ts_str = f"{curr_dt.isoformat()}T{hour:02d}:00:00"
                    act = base_act + random.uniform(-15.0, 15.0)
                    rum = (base_rum / 6.0) + random.uniform(-10.0, 10.0)
                    temp = base_temp + random.uniform(-0.2, 0.2)
                    stbm = 0
                    mounts_p = 0
                    mounts_r = 0

                    if is_estrus_day and hour in [8, 12, 16]:
                        act *= random.uniform(2.2, 3.1)  # Vigorous activity surge
                        rum *= random.uniform(0.4, 0.6)  # Rumination drop
                        stbm = random.randint(1, 3)
                        mounts_p = random.randint(2, 5)
                        mounts_r = random.randint(1, 4)
                        temp += 0.5

                    if is_fever_day and hour in [8, 12, 16]:
                        temp = round(39.8 + random.uniform(0.0, 0.6), 1)
                        act *= 0.6
                        rum *= 0.5

                    sensor_obs.append({
                        "observation_id": f"OBS-{obs_id_cnt:06d}",
                        "animal_id": cow_id,
                        "timestamp": ts_str,
                        "sensor_id": f"SENS-COLLAR-{c_idx:03d}",
                        "observation_interval_minutes": 240,
                        "activity_count": round(act, 1),
                        "step_count": round(act * 8.5, 0),
                        "standing_time_min": round(random.uniform(60, 120), 1),
                        "lying_time_min": round(random.uniform(80, 140), 1),
                        "rumination_time_min": round(max(rum, 5.0), 1),
                        "feeding_time_min": round(random.uniform(25, 50), 1),
                        "mounts_performed": mounts_p,
                        "mounts_received": mounts_r,
                        "standing_to_be_mounted_count": stbm,
                        "body_temperature_c": round(temp, 1),
                        "temperature_method": "reticular_bolus",
                        "temperature_site": "reticulum",
                        "respiratory_rate_breaths_min": round(random.uniform(24, 38), 1),
                        "water_intake_l": round(random.uniform(15, 25), 1),
                        "feed_intake_kg": round(random.uniform(8, 14), 1),
                        "feed_measurement_basis": "dry_matter",
                        "data_source": "telemetry_collar",
                        "quality_status": "valid",
                        "quality_notes": None
                    })
                    obs_id_cnt += 1

                # Milk records for lactating cows (Daily morning and evening sessions)
                if c_idx <= 8 and day % 2 == 0:
                    m_yield = round(random.uniform(12.0, 18.0), 1)
                    e_yield = round(random.uniform(10.0, 15.0), 1)
                    scc = 120000.0 + random.uniform(-30000, 40000)
                    if is_mastitis_day:
                        m_yield *= 0.65
                        e_yield *= 0.65
                        scc = 650000.0

                    milk_records.append({
                        "milk_record_id": f"MILK-{milk_id_cnt:05d}",
                        "animal_id": cow_id,
                        "record_datetime": f"{curr_dt.isoformat()}T06:30:00",
                        "milking_session": "morning",
                        "record_type": "session",
                        "morning_yield_l": m_yield,
                        "evening_yield_l": None,
                        "total_yield_l": m_yield,
                        "milk_conductivity": 5.4,
                        "somatic_cell_count": round(scc, 0),
                        "milk_appearance": "normal" if not is_mastitis_day else "clots",
                        "data_source": "parlor_meter",
                        "remarks": "Standard milking"
                    })
                    milk_id_cnt += 1

                # Periodic BCS Assessment (every 30 days)
                if day in [0, 30, 60]:
                    bcs_records.append({
                        "bcs_record_id": f"BCS-{bcs_id_cnt:04d}",
                        "animal_id": cow_id,
                        "assessment_date": curr_dt.isoformat(),
                        "bcs_value": round(random.choice([2.75, 3.0, 3.25, 3.5]), 2),
                        "assessor": "Dr. Sharma",
                        "assessment_method": "visual_palpation",
                        "lactation_stage": "mid_lactation",
                        "body_weight_kg": round(580.0 + random.uniform(-20, 20), 1),
                        "remarks": "Adequate body reserve"
                    })
                    bcs_id_cnt += 1

        self._write_csv("sensor_observations.csv", sensor_obs)
        self._write_csv("educational_ground_truth.csv", ground_truth)
        self._write_csv("milk_records.csv", milk_records)
        self._write_csv("bcs_records.csv", bcs_records)

        # 4. Reproductive Events and AI Records
        repro_events.append({
            "event_id": "EVT-001",
            "animal_id": "COW-001",
            "event_datetime": "2026-01-22T08:00:00",
            "event_type": "confirmed_estrus",
            "event_source": "visual_and_collar",
            "observation_notes": "Standing heat observed at morning feeding.",
            "confirmation_status": "confirmed",
            "confirmed_by": "Herdsman Rajiv",
            "confirmation_datetime": "2026-01-22T09:00:00",
            "linked_prediction_id": None
        })
        ai_records.append({
            "ai_id": "AI-001",
            "animal_id": "COW-001",
            "event_id": "EVT-001",
            "ai_datetime": "2026-01-22T17:30:00",
            "semen_bull_id": "BULL-001",
            "semen_batch_id": "LOT-2025-HF-09",
            "technician": "Veterinary Officer Dr. Anil",
            "ai_attempt_number": 1,
            "ai_type": "frozen_semen_straw",
            "conception_method": "AI",
            "outcome_status": "pending",
            "remarks": "Clean cervical deposition; AM-PM rule followed."
        })
        self._write_csv("reproductive_events.csv", repro_events)
        self._write_csv("ai_records.csv", ai_records)

        # 5. Pregnancy Records
        preg_records = [{
            "pregnancy_id": "PRG-001",
            "animal_id": "COW-003",
            "ai_id": None,
            "examination_date": "2026-02-15",
            "examination_method": "transrectal_ultrasonography",
            "pregnancy_status": "confirmed_pregnant",
            "estimated_days_pregnant": 65,
            "estimated_due_date": "2026-09-17",
            "conception_date": "2025-12-12",
            "conception_date_status": "estimated",
            "veterinarian_id": "Dr. Verma",
            "notes": "Single viable fetus with active cardiac heartbeat."
        }]
        self._write_csv("pregnancy_records.csv", preg_records)

        # 6. Calving Records
        calving_records = [{
            "calving_id": "CALV-001",
            "dam_id": "COW-001",
            "calving_datetime": "2026-01-15T04:30:00",
            "ai_id": None,
            "conception_method": "AI",
            "calving_type": "unassisted_eutocia",
            "calf_count": 1,
            "calving_outcome": "live_birth",
            "complications": "none",
            "veterinarian_id": "Dr. Sharma",
            "remarks": "Heifer calf delivered without traction."
        }]
        self._write_csv("calving_records.csv", calving_records)

        # 7. Health Observations
        health_obs.append({
            "health_observation_id": "HLTH-001",
            "animal_id": "COW-005",
            "observation_datetime": "2026-01-30T09:00:00",
            "body_temperature_c": 39.9,
            "temperature_method": "rectal",
            "respiratory_rate_breaths_min": 44.0,
            "feed_intake_status": "decreased",
            "water_intake_status": "normal",
            "cough": 1,
            "nasal_discharge": 1,
            "ocular_discharge": 0,
            "letargy": 1,
            "udder_swelling": 0,
            "abnormal_milk": 0,
            "udder_pain": 0,
            "manure_abnormality": "none",
            "observed_by": "Herdsman Rajiv",
            "data_source": "routine_morning_inspection",
            "notes": "Mild serous nasal discharge and dull demeanor."
        })
        self._write_csv("health_observations.csv", health_obs)

        # 8. Health Alerts
        health_alerts.append({
            "alert_id": "ALT-001",
            "animal_id": "COW-005",
            "alert_datetime": "2026-01-30T09:15:00",
            "alert_category": "fever_screening",
            "priority": "high",
            "alert_score": 39.9,
            "triggering_parameters": '{"body_temperature_c": 39.9, "threshold": 39.5, "is_calf": false}',
            "current_status": "active",
            "veterinarian_notes": "Prescribed supportive electrolytes; isolated in hospital pen.",
            "resolution_datetime": None,
            "linked_health_event_id": "HLTH-001"
        })
        self._write_csv("health_alerts.csv", health_alerts)

        # 9. Calf Care Records
        calf_care = [
            {
                "care_record_id": "CARE-001",
                "animal_id": "CALF-001",
                "event_datetime": "2026-01-15T06:00:00",
                "care_type": "colostrum_feeding",
                "quantity": 3.5,
                "quantity_unit": "liters",
                "colostrum_brix_pct": 24.5,
                "vaccination_name": None,
                "medication_name": None,
                "administered_by": "Calf Specialist Meena",
                "notes": "Fed within 2 hours of parturition via nipple bottle."
            },
            {
                "care_record_id": "CARE-002",
                "animal_id": "CALF-001",
                "event_datetime": "2026-01-15T05:00:00",
                "care_type": "navel_antisepsis",
                "quantity": 1.0,
                "quantity_unit": "application",
                "colostrum_brix_pct": None,
                "vaccination_name": None,
                "medication_name": "7% Tincture of Iodine",
                "administered_by": "Calf Specialist Meena",
                "notes": "Navel dipped thoroughly."
            }
        ]
        self._write_csv("calf_care_records.csv", calf_care)

        return {
            "status": "success",
            "datasets_generated": 13,
            "output_dir": str(self.sample_dir)
        }

    def _write_csv(self, filename: str, rows: List[Dict[str, Any]]) -> None:
        if not rows:
            return
        filepath = self.sample_dir / filename
        fieldnames = list(rows[0].keys())
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
