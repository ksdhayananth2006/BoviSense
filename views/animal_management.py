"""
BOVISENSE Page: Animal Registration and Individual Profiles (Module 2)
Provides full registry browsing, registration, editing, and comprehensive biological profiles.
"""
import datetime
import pandas as pd
import streamlit as pd_st
import streamlit as st

from components.cards import render_disclaimer
from components.charts import plot_sensor_timeseries, plot_milk_trends
from database.db_manager import db
from database.repositories import AnimalRepository, SensorRepository, MilkAndBCSRepository
from services.dataset_manager import DatasetManager


def show():
    st.title("🐄 Animal Registration & Individual Profiles")
    st.caption("Manage individual cattle records, pedigree associations, and longitudinal biological profiles.")

    animal_repo = AnimalRepository()
    sensor_repo = SensorRepository()
    milk_repo = MilkAndBCSRepository()

    tab_browse, tab_profile, tab_register = st.tabs(["Browse Herd", "Individual Biological Profile", "Register New Animal"])

    # TAB 1: BROWSE HERD
    with tab_browse:
        st.subheader("Herd Directory")
        c1, c2, c3 = st.columns(3)
        with c1:
            search_term = st.text_input("🔍 Search by ID or Name", "")
        with c2:
            type_filter = st.selectbox("Animal Type", ["All", "cow", "bull", "calf", "heifer", "steer"])
        with c3:
            status_filter = st.selectbox("Status", ["active", "sold", "culled", "deceased", "All"])

        query = "SELECT * FROM animals WHERE 1=1"
        params = []
        if search_term.strip():
            query += " AND (animal_id LIKE ? OR animal_name LIKE ?)"
            params.extend([f"%{search_term.strip()}%", f"%{search_term.strip()}%"])
        if type_filter != "All":
            query += " AND animal_type = ?"
            params.append(type_filter)
        if status_filter != "All":
            query += " AND animal_status = ?"
            params.append(status_filter)

        query += " ORDER BY animal_id ASC"
        animals = db.fetchall(query, params)

        if animals:
            df = pd.DataFrame(animals)
            cols_to_show = ["animal_id", "animal_name", "animal_type", "sex", "breed", "dob", "current_weight_kg", "reproductive_status", "health_status", "barn_id"]
            st.dataframe(df[cols_to_show], use_container_width=True)
            st.caption(f"Showing {len(animals)} animals matching filter criteria.")
        else:
            st.info("No animals found matching criteria.")

    # TAB 2: INDIVIDUAL PROFILE
    with tab_profile:
        st.subheader("Comprehensive Animal Profile")
        all_ids = [a["animal_id"] for a in animal_repo.get_all(status=None)]
        if not all_ids:
            st.info("No animals in database to inspect.")
        else:
            selected_id = st.selectbox("Select Animal to Inspect", all_ids)
            animal = animal_repo.get_by_id(selected_id)

            if animal:
                # Header Information
                c_head1, c_head2, c_head3, c_head4 = st.columns(4)
                with c_head1:
                    st.write(f"**ID:** {animal['animal_id']}")
                    st.write(f"**Name:** {animal.get('animal_name') or 'N/A'}")
                    st.write(f"**Breed:** {animal['breed']}")
                with c_head2:
                    st.write(f"**Type:** {animal['animal_type'].title()}")
                    st.write(f"**Sex:** {animal['sex']}")
                    st.write(f"**DOB:** {animal['dob']}")
                with c_head3:
                    st.write(f"**Dam:** {animal.get('dam_id') or 'Unknown'}")
                    st.write(f"**Sire:** {animal.get('sire_id') or 'Unknown'}")
                    st.write(f"**Barn:** {animal.get('barn_id') or 'Unassigned'}")
                with c_head4:
                    st.write(f"**Reproductive:** {animal.get('reproductive_status')}")
                    st.write(f"**Health:** {animal.get('health_status')}")
                    st.write(f"**Current Weight:** {animal.get('current_weight_kg') or 'N/A'} kg")

                st.markdown("---")

                # Profile History Tabs
                ptab_sensor, ptab_repro, ptab_health, ptab_milk, ptab_calves = st.tabs([
                    "Sensor Observations", "Reproductive & AI History", "Health & Screening", "Milk & BCS", "Offspring / Calves"
                ])

                with ptab_sensor:
                    sensor_recs = sensor_repo.get_observations(selected_id)
                    st.write(f"Found {len(sensor_recs)} sensor observation records.")
                    if sensor_recs:
                        sdf = pd.DataFrame(sensor_recs)
                        st.plotly_chart(plot_sensor_timeseries(sdf, selected_id), use_container_width=True)
                        with st.expander("View Raw Sensor Data Table"):
                            st.dataframe(sdf, use_container_width=True)
                    else:
                        st.caption("No sensor telemetry recorded for this animal.")

                with ptab_repro:
                    r_events = db.fetchall("SELECT * FROM reproductive_events WHERE animal_id = ? ORDER BY event_datetime DESC", (selected_id,))
                    ai_recs = db.fetchall("SELECT * FROM ai_records WHERE animal_id = ? ORDER BY ai_datetime DESC", (selected_id,))
                    preg_recs = db.fetchall("SELECT * FROM pregnancy_records WHERE animal_id = ? ORDER BY examination_date DESC", (selected_id,))

                    col_r1, col_r2 = st.columns(2)
                    with col_r1:
                        st.write(f"**Reproductive Events ({len(r_events)})**")
                        if r_events:
                            st.dataframe(pd.DataFrame(r_events)[["event_id", "event_datetime", "event_type", "confirmation_status"]], use_container_width=True)
                        else:
                            st.caption("No reproductive events.")

                        st.write(f"**AI Services ({len(ai_recs)})**")
                        if ai_recs:
                            st.dataframe(pd.DataFrame(ai_recs)[["ai_id", "ai_datetime", "semen_bull_id", "outcome_status"]], use_container_width=True)
                        else:
                            st.caption("No AI records.")

                    with col_r2:
                        st.write(f"**Pregnancy Examinations ({len(preg_recs)})**")
                        if preg_recs:
                            st.dataframe(pd.DataFrame(preg_recs)[["pregnancy_id", "examination_date", "pregnancy_status", "estimated_due_date"]], use_container_width=True)
                        else:
                            st.caption("No pregnancy diagnoses recorded.")

                with ptab_health:
                    h_obs = db.fetchall("SELECT * FROM health_observations WHERE animal_id = ? ORDER BY observation_datetime DESC", (selected_id,))
                    h_alts = db.fetchall("SELECT * FROM health_alerts WHERE animal_id = ? ORDER BY alert_datetime DESC", (selected_id,))

                    st.write(f"**Active and Historical Health Alerts ({len(h_alts)})**")
                    if h_alts:
                        st.dataframe(pd.DataFrame(h_alts)[["alert_id", "alert_datetime", "alert_category", "priority", "current_status"]], use_container_width=True)
                    else:
                        st.caption("No health alerts on file.")

                    st.write(f"**Clinical Observations ({len(h_obs)})**")
                    if h_obs:
                        st.dataframe(pd.DataFrame(h_obs), use_container_width=True)
                    else:
                        st.caption("No clinical observations logged.")

                with ptab_milk:
                    m_recs = milk_repo.get_milk_records(selected_id)
                    b_recs = milk_repo.get_bcs_records(selected_id)
                    st.write(f"**Milk Production ({len(m_recs)} records)**")
                    if m_recs:
                        from services.milk_analyzer import MilkAnalyzer
                        daily_df = MilkAnalyzer.aggregate_daily_yields(m_recs)
                        st.plotly_chart(plot_milk_trends(daily_df), use_container_width=True)
                    else:
                        st.caption("No milk records for this animal.")

                    st.write(f"**Body Condition Scores ({len(b_recs)} records)**")
                    if b_recs:
                        st.dataframe(pd.DataFrame(b_recs)[["bcs_record_id", "assessment_date", "bcs_value", "assessor"]], use_container_width=True)
                    else:
                        st.caption("No BCS records.")

                with ptab_calves:
                    offspring = db.fetchall("SELECT * FROM animals WHERE dam_id = ? OR sire_id = ?", (selected_id, selected_id))
                    st.write(f"**Direct Offspring ({len(offspring)})**")
                    if offspring:
                        st.dataframe(pd.DataFrame(offspring)[["animal_id", "animal_name", "dob", "sex", "breed", "animal_status"]], use_container_width=True)
                    else:
                        st.caption("No registered offspring for this animal.")

                st.markdown("---")
                with st.expander("🗑️ Danger Zone: Delete Animal Record"):
                    st.warning("Deleting an animal requires that all dependent sensor, health, and calving records are cleared first.")
                    if st.button("Delete This Animal", key=f"del_anim_{selected_id}"):
                        success, msg = DatasetManager.delete_record("animals", selected_id)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

    # TAB 3: REGISTER NEW ANIMAL
    with tab_register:
        st.subheader("New Animal Registration Form")
        with st.form("new_animal_form", clear_on_submit=True):
            fc1, fc2, fc3 = st.columns(3)
            with fc1:
                n_id = st.text_input("Animal ID *", placeholder="e.g. COW-045")
                n_name = st.text_input("Animal Name", placeholder="e.g. Daisy")
                n_type = st.selectbox("Animal Type *", ["cow", "bull", "calf", "heifer", "steer"])
            with fc2:
                n_sex = st.selectbox("Sex *", ["F", "M"])
                n_breed = st.text_input("Breed *", value="Holstein-Friesian")
                n_dob = st.date_input("Date of Birth *", value=datetime.date(2023, 1, 1))
            with fc3:
                n_dam = st.text_input("Dam ID (Optional)", placeholder="e.g. COW-001")
                n_sire = st.text_input("Sire ID (Optional)", placeholder="e.g. BULL-001")
                n_weight = st.number_input("Current Weight (kg)", min_value=0.0, max_value=1500.0, value=450.0, step=0.5)

            fc4, fc5 = st.columns(2)
            with fc4:
                n_repro = st.selectbox("Reproductive Status", ["open", "bred", "pregnant", "dry", "lactating", "not_eligible"])
                n_health = st.selectbox("Health Status", ["healthy", "under_observation", "sick", "quarantined"])
            with fc5:
                n_barn = st.selectbox("Barn Assignment", ["BARN-A", "BARN-B", "BARN-C", "BARN-D", "None"])
                n_remarks = st.text_area("Remarks", "")

            submitted = st.form_submit_button("Register Animal")
            if submitted:
                if not n_id.strip():
                    st.error("Animal ID is required.")
                else:
                    new_animal_data = {
                        "animal_id": n_id.strip(),
                        "animal_name": n_name.strip() if n_name.strip() else None,
                        "animal_type": n_type,
                        "sex": n_sex,
                        "breed": n_breed.strip(),
                        "dob": n_dob.isoformat(),
                        "acquisition_type": "born_on_farm",
                        "acquisition_date": n_dob.isoformat(),
                        "dam_id": n_dam.strip() if n_dam.strip() else None,
                        "sire_id": n_sire.strip() if n_sire.strip() else None,
                        "birth_weight_kg": None,
                        "current_weight_kg": float(n_weight) if n_weight > 0 else None,
                        "parity": 0,
                        "lactation_number": 0,
                        "reproductive_status": n_repro,
                        "health_status": n_health,
                        "animal_status": "active",
                        "barn_id": n_barn if n_barn != "None" else None,
                        "remarks": n_remarks.strip() if n_remarks.strip() else None
                    }
                    success, msg = DatasetManager.add_record("animals", new_animal_data)
                    if success:
                        st.success(f"Animal {n_id} successfully registered!")
                    else:
                        st.error(msg)
