"""
BOVISENSE Page: Cattle Health Monitoring and Alerts (Module 6)
Multi-parameter clinical screening, alert deduplication, priority management,
veterinary action notes, and resolution auditing.
"""
import datetime
import json
import pandas as pd
import streamlit as st

from components.cards import render_disclaimer, render_health_alert_badge
from database.db_manager import db
from database.repositories import HealthRepository
from services.dataset_manager import DatasetManager
from services.health_monitor import HEALTH_DISCLAIMER, HealthMonitor


def show():
    st.title("🩺 Cattle Health Monitoring & Alerts")
    st.caption("Veterinary clinical screening, multi-symptom surveillance, alert resolution, and health observations.")

    render_disclaimer(HEALTH_DISCLAIMER, "error")

    health_repo = HealthRepository()
    health_monitor = HealthMonitor(health_repo)

    tab_alerts, tab_obs, tab_screen = st.tabs(["Active & Resolved Alerts", "Clinical Observations Log", "Screen Health Observation"])

    # TAB 1: ALERTS MANAGEMENT
    with tab_alerts:
        st.subheader("Clinical Health Alerts")

        c1, c2 = st.columns(2)
        with c1:
            status_filter = st.selectbox("Alert Status", ["active", "resolved", "All"])
        with c2:
            cat_filter = st.selectbox("Category", ["All", "fever_screening", "respiratory_screening", "mastitis_screening", "heat_stress"])

        query = "SELECT * FROM health_alerts WHERE 1=1"
        params = []
        if status_filter != "All":
            query += " AND current_status = ?"
            params.append(status_filter)
        if cat_filter != "All":
            query += " AND alert_category = ?"
            params.append(cat_filter)
        query += " ORDER BY alert_datetime DESC"

        alerts = db.fetchall(query, params)
        if alerts:
            for alt in alerts:
                aid = alt["alert_id"]
                with st.expander(f"{alt['priority'].upper()} • {alt['alert_category'].replace('_', ' ').title()} — {alt['animal_id']} ({alt['alert_datetime']})"):
                    col_a1, col_a2 = st.columns(2)
                    with col_a1:
                        st.write(f"**Alert ID:** `{aid}`")
                        st.write(f"**Animal:** `{alt['animal_id']}`")
                        st.write(f"**Status:** `{alt['current_status']}`")
                        st.write(f"**Score / Metric:** `{alt['alert_score']}`")
                    with col_a2:
                        st.write("**Triggering Clinical Parameters:**")
                        try:
                            st.json(json.loads(alt["triggering_parameters"]))
                        except Exception:
                            st.write(alt["triggering_parameters"])

                    if alt["current_status"] == "resolved":
                        st.success(f"Resolved on {alt.get('resolution_datetime')}. Vet Notes: {alt.get('veterinarian_notes')}")
                    else:
                        st.markdown("---")
                        st.write("**Resolve Alert (Veterinary Action)**")
                        with st.form(f"resolve_form_{aid}"):
                            vet_notes = st.text_area("Veterinarian Examination & Resolution Notes", placeholder="e.g. Examined animal. Administered oral flunixin; symptoms resolved.")
                            submit_resolve = st.form_submit_button("Mark Alert as Resolved")
                            if submit_resolve and vet_notes.strip():
                                health_repo.resolve_alert(aid, vet_notes.strip())
                                st.success("Alert successfully marked as resolved!")
                                st.rerun()
        else:
            st.info("No health alerts matching current filter.")

    # TAB 2: CLINICAL OBSERVATIONS LOG
    with tab_obs:
        st.subheader("Historical Clinical Observations")
        h_obs = db.fetchall("SELECT * FROM health_observations ORDER BY observation_datetime DESC LIMIT 200")
        if h_obs:
            df = pd.DataFrame(h_obs)
            cols_disp = ["health_observation_id", "animal_id", "observation_datetime", "body_temperature_c", "respiratory_rate_breaths_min", "cough", "nasal_discharge", "letargy", "abnormal_milk"]
            st.dataframe(df[cols_disp], use_container_width=True)
        else:
            st.info("No clinical observations logged.")

    # TAB 3: SCREEN HEALTH OBSERVATION
    with tab_screen:
        st.subheader("Run Multi-Symptom Clinical Screening")
        st.caption("Submit clinical observation parameters to check against rule-based screening thresholds.")

        animals = db.fetchall("SELECT animal_id, animal_type FROM animals ORDER BY animal_id")
        animal_ids = [a["animal_id"] for a in animals]

        with st.form("screen_health_form"):
            sc1, sc2, sc3 = st.columns(3)
            with sc1:
                sel_a = st.selectbox("Animal ID *", animal_ids if animal_ids else [""])
                obs_dt = st.text_input("Observation Datetime", datetime.datetime.now().isoformat())
                obs_by = st.text_input("Observed By", "Dr. Sharma")
            with sc2:
                s_temp = st.number_input("Body Temp (°C)", min_value=34.0, max_value=45.0, value=38.6, step=0.1)
                s_resp = st.number_input("Respiratory Rate (breaths/min)", min_value=10.0, max_value=150.0, value=30.0, step=1.0)
                s_scc = st.number_input("Somatic Cell Count (cells/mL)", min_value=0.0, max_value=5000000.0, value=120000.0, step=10000.0)
            with sc3:
                s_cough = st.checkbox("Cough Observed", value=False)
                s_nasal = st.checkbox("Nasal Discharge Present", value=False)
                s_swelling = st.checkbox("Udder Swelling Present", value=False)
                s_milk = st.checkbox("Abnormal Milk (Clots/Watery)", value=False)

            s_notes = st.text_area("Clinical Notes", "")
            submit_screen = st.form_submit_button("Run Health Screening")

            if submit_screen and sel_a:
                # Determine if calf
                a_type = next((a["animal_type"] for a in animals if a["animal_id"] == sel_a), "cow")
                is_calf = (a_type == "calf")

                # Insert observation
                h_id = f"HLTH-{datetime.datetime.now().strftime('%H%M%S')}"
                obs_dict = {
                    "health_observation_id": h_id,
                    "animal_id": sel_a,
                    "observation_datetime": obs_dt,
                    "body_temperature_c": s_temp,
                    "temperature_method": "rectal",
                    "respiratory_rate_breaths_min": s_resp,
                    "feed_intake_status": "normal",
                    "water_intake_status": "normal",
                    "cough": 1 if s_cough else 0,
                    "nasal_discharge": 1 if s_nasal else 0,
                    "ocular_discharge": 0,
                    "letargy": 0,
                    "udder_swelling": 1 if s_swelling else 0,
                    "abnormal_milk": 1 if s_milk else 0,
                    "udder_pain": 0,
                    "manure_abnormality": "none",
                    "observed_by": obs_by,
                    "data_source": "clinical_examination",
                    "notes": s_notes
                }
                health_repo.insert_observation(obs_dict)

                # Screen
                triggered = health_monitor.screen_health_observation(
                    animal_id=sel_a,
                    obs=obs_dict,
                    is_calf=is_calf
                )

                st.success(f"Observation logged as `{h_id}`!")
                if triggered:
                    st.warning(f"⚠️ **{len(triggered)} Screening Alert(s) Triggered!**")
                    for alt in triggered:
                        render_health_alert_badge(alt["priority"], alt["alert_category"])
                        st.json(json.loads(alt["triggering_parameters"]))
                else:
                    st.info("No clinical alert criteria met. Vitals remain within nominal screening ranges.")
