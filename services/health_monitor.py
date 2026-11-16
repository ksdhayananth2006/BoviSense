"""
BOVISENSE Cattle Health Screening and Alert Engine
Implements multi-parameter clinical screening, alert deduplication, and resolution tracking.
"""
import datetime
import json
import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple

from config.thresholds import HEALTH_THRESHOLDS
from database.repositories import HealthRepository

logger = logging.getLogger("bovisense.health")

HEALTH_DISCLAIMER = (
    "BOVISENSE provides biological monitoring and preliminary screening indicators. "
    "It does not replace veterinary examination, laboratory testing or professional diagnosis."
)


class HealthMonitor:
    """Manages clinical rule screening and deduplicated health alerts."""

    def __init__(self, health_repo: Optional[HealthRepository] = None):
        self.health_repo = health_repo or HealthRepository()

    def screen_health_observation(
        self,
        animal_id: str,
        obs: Dict[str, Any],
        is_calf: bool = False,
        thi_value: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Evaluates a health or sensor observation against multi-symptom clinical screening criteria.
        Returns newly triggered health alerts (deduplicated against existing active alerts).
        """
        generated_alerts: List[Dict[str, Any]] = []
        obs_time = obs.get("observation_datetime") or obs.get("timestamp") or datetime.datetime.now(datetime.timezone.utc).isoformat()

        # 1. Fever Screening
        temp = obs.get("body_temperature_c")
        if temp is not None:
            t = float(temp)
            fever_cutoff = HEALTH_THRESHOLDS["calf_fever_temp_c"] if is_calf else HEALTH_THRESHOLDS["adult_fever_temp_c"]
            if t >= fever_cutoff:
                existing = self.health_repo.check_duplicate_active_alert(animal_id, "fever_screening")
                if not existing:
                    priority = "high" if t >= (fever_cutoff + 1.0) else "medium"
                    alert = self._create_alert(
                        animal_id=animal_id,
                        obs_time=obs_time,
                        category="fever_screening",
                        priority=priority,
                        score=round(t, 2),
                        trigger={"body_temperature_c": t, "threshold": fever_cutoff, "is_calf": is_calf}
                    )
                    generated_alerts.append(alert)

        # 2. Respiratory Screening
        resp_rate = obs.get("respiratory_rate_breaths_min")
        cough = int(obs.get("cough") or 0)
        nasal = int(obs.get("nasal_discharge") or 0)
        ocular = int(obs.get("ocular_discharge") or 0)

        is_resp_elevated = (resp_rate is not None and float(resp_rate) >= HEALTH_THRESHOLDS["elevated_respiratory_rate_bpm"])
        has_resp_symptoms = (cough > 0 or nasal > 0 or ocular > 0)

        if is_resp_elevated or has_resp_symptoms:
            existing = self.health_repo.check_duplicate_active_alert(animal_id, "respiratory_screening")
            if not existing:
                priority = "high" if (is_resp_elevated and has_resp_symptoms) else "medium"
                score = (float(resp_rate) if resp_rate else 40.0) + (cough + nasal + ocular) * 10
                alert = self._create_alert(
                    animal_id=animal_id,
                    obs_time=obs_time,
                    category="respiratory_screening",
                    priority=priority,
                    score=round(score, 1),
                    trigger={"respiratory_rate": resp_rate, "cough": cough, "nasal": nasal, "ocular": ocular}
                )
                generated_alerts.append(alert)

        # 3. Mastitis Screening
        udder_swelling = int(obs.get("udder_swelling") or 0)
        udder_pain = int(obs.get("udder_pain") or 0)
        abnormal_milk = int(obs.get("abnormal_milk") or 0)
        scc = obs.get("somatic_cell_count")

        scc_elevated = (scc is not None and float(scc) >= HEALTH_THRESHOLDS["subclinical_mastitis_scc"])
        clinical_signs = (udder_swelling > 0 or udder_pain > 0 or abnormal_milk > 0)

        if scc_elevated or clinical_signs:
            existing = self.health_repo.check_duplicate_active_alert(animal_id, "mastitis_screening")
            if not existing:
                priority = "critical" if (clinical_signs and scc_elevated) else ("high" if clinical_signs else "medium")
                score = float(scc) / 1000.0 if scc else 100.0
                alert = self._create_alert(
                    animal_id=animal_id,
                    obs_time=obs_time,
                    category="mastitis_screening",
                    priority=priority,
                    score=round(score, 1),
                    trigger={"scc": scc, "udder_swelling": udder_swelling, "abnormal_milk": abnormal_milk, "udder_pain": udder_pain}
                )
                generated_alerts.append(alert)

        # 4. Environmental Heat Stress Screening
        if thi_value is not None and thi_value >= 78.0:
            existing = self.health_repo.check_duplicate_active_alert(animal_id, "heat_stress")
            if not existing:
                priority = "high" if thi_value >= 84.0 else "medium"
                alert = self._create_alert(
                    animal_id=animal_id,
                    obs_time=obs_time,
                    category="heat_stress",
                    priority=priority,
                    score=round(thi_value, 1),
                    trigger={"thi_value": thi_value, "body_temperature_c": temp, "respiratory_rate": resp_rate}
                )
                generated_alerts.append(alert)

        return generated_alerts

    def _create_alert(
        self,
        animal_id: str,
        obs_time: str,
        category: str,
        priority: str,
        score: float,
        trigger: Dict[str, Any]
    ) -> Dict[str, Any]:
        alert_id = f"alt_{uuid.uuid4().hex[:12]}"
        alert_data = {
            "alert_id": alert_id,
            "animal_id": animal_id,
            "alert_datetime": obs_time,
            "alert_category": category,
            "priority": priority,
            "alert_score": score,
            "triggering_parameters": json.dumps(trigger),
            "current_status": "active",
            "veterinarian_notes": "",
            "resolution_datetime": None,
            "linked_health_event_id": None
        }
        self.health_repo.insert_alert(alert_data)
        logger.info(f"Generated {priority} {category} alert for {animal_id}")
        return alert_data
