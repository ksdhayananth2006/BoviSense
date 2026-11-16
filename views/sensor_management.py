"""
BOVISENSE Page: Sensor Data Management (Module 3)
Manages sensor hardware registry, multi-metric time-series visualizations, and data-quality audits.
"""
import datetime
import pandas as pd
import streamlit as st

from components.cards import render_disclaimer
from components.charts import plot_sensor_timeseries
from config.settings import QUALITY_STATUSES
from database.db_manager import db
from database.repositories import SensorRepository
from services.dataset_manager import DatasetManager


def show():
    st.title("📡 Sensor Data Management")
    st.caption("Electronic monitoring telemetry, quality auditing, sensor metadata, and time-series analytics.")

    sensor_repo = SensorRepository()

    tab_vis, tab_registry, tab_entry = st.tabs(["Telemetry Visualizer", "Sensor Registry", "Manual Observation Entry"])

    # TAB 1: TELEMETRY VISUALIZER
    with tab_vis:
        st.subheader("Sensor Observation Time-Series")

        c1, c2, c3 = st.columns(3)
        with c1:
            animals = db.fetchall("SELECT animal_id FROM animals ORDER BY animal_id")
            animal_ids = [a["animal_id"] for a in animals]
            selected_animal = st.selectbox("Select Animal", animal_ids if animal_ids else ["None"])
        with c2:
            quality_filter = st.selectbox("Quality Status", ["All"] + QUALITY_STATUSES)
        with c3:
            limit_records = st.selectbox("Max Records to Display", [100, 250, 500, 1000, 5000], index=1)

        if selected_animal and selected_animal != "None":
            query = "SELECT * FROM sensor_observations WHERE animal_id = ?"
            params = [selected_animal]
            if quality_filter != "All":
                query += " AND quality_status = ?"
                params.append(quality_filter)
            query += " ORDER BY timestamp ASC LIMIT ?"
            params.append(limit_records)

            obs = db.fetchall(query, params)
            if obs:
                df = pd.DataFrame(obs)
                st.plotly_chart(plot_sensor_timeseries(df, selected_animal), use_container_width=True)

                # Quality and Missing Data Audit
                with st.expander("📊 Data Quality & Missing Data Summary"):
                    col_q1, col_q2 = st.columns(2)
                    with col_q1:
                        st.write("**Observations Quality Classification**")
                        st.dataframe(df["quality_status"].value_counts().reset_index(), use_container_width=True)
                    with col_q2:
                        st.write("**Missing Values per Metric (Non-zero null count)**")
                        missing_summary = df[["activity_count", "rumination_time_min", "body_temperature_c", "standing_time_min"]].isnull().sum().reset_index()
                        missing_summary.columns = ["Metric", "Missing Count"]
                        st.dataframe(missing_summary, use_container_width=True)

                st.subheader(f"Observation Records ({len(df)})")
                st.dataframe(df, use_container_width=True)

                # CSV Export of filtered view
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label="📥 Export Filtered Observations (CSV)",
                    data=csv_data,
                    file_name=f"sensor_obs_{selected_animal}.csv",
                    mime="text/csv"
                )
            else:
                st.info(f"No sensor records found for {selected_animal} under selected filters.")
        else:
            st.info("No animals available.")

    # TAB 2: SENSOR REGISTRY
    with tab_registry:
        st.subheader("Active Sensors Hardware Registry")
        sensors = sensor_repo.get_all_sensors()
        if sensors:
            st.dataframe(pd.DataFrame(sensors), use_container_width=True)
        else:
            st.info("No sensors currently cataloged.")

        with st.expander("Register New Hardware Sensor"):
            with st.form("new_sensor_form"):
                sc1, sc2 = st.columns(2)
                with sc1:
                    s_id = st.text_input("Sensor ID *", placeholder="e.g. SENS-BOLUS-001")
                    s_name = st.text_input("Sensor Name", placeholder="e.g. Reticular Bolus Sensor #1")
                    s_type = st.selectbox("Sensor Type", ["neck_collar", "reticular_bolus", "ear_tag", "leg_pedometer", "barn_ambient_station"])
                with sc2:
                    s_manuf = st.text_input("Manufacturer", "BoviSense Tech")
                    s_model = st.text_input("Model", "BioTrack-V2")
                    s_unit = st.text_input("Measurement Unit", "counts_minutes")
                
                s_submit = st.form_submit_button("Save Sensor")
                if s_submit and s_id.strip():
                    sensor_repo.insert_sensor({
                        "sensor_id": s_id.strip(),
                        "sensor_name": s_name.strip(),
                        "sensor_type": s_type,
                        "manufacturer": s_manuf,
                        "model": s_model,
                        "measurement_type": s_type,
                        "measurement_unit": s_unit,
                        "installation_date": datetime.date.today().isoformat(),
                        "calibration_date": datetime.date.today().isoformat(),
                        "sensor_status": "active",
                        "notes": "Added via interface"
                    })
                    st.success(f"Sensor {s_id} registered!")
                    st.rerun()

    # TAB 3: MANUAL OBSERVATION ENTRY
    with tab_entry:
        st.subheader("Log Manual Sensor Observation")
        with st.form("manual_sensor_form"):
            mc1, mc2, mc3 = st.columns(3)
            with mc1:
                m_obs_id = st.text_input("Observation ID *", f"MAN-OBS-{datetime.datetime.now().strftime('%H%M%S')}")
                m_anim = st.selectbox("Animal ID *", animal_ids if animal_ids else [""])
                m_time = st.text_input("Timestamp (ISO 8601)", datetime.datetime.now().isoformat())
            with mc2:
                m_act = st.number_input("Activity Count", min_value=0.0, max_value=2000.0, value=100.0)
                m_rum = st.number_input("Rumination Time (min)", min_value=0.0, max_value=240.0, value=35.0)
                m_temp = st.number_input("Body Temperature (°C)", min_value=34.0, max_value=45.0, value=38.6)
            with mc3:
                m_stbm = st.number_input("Standing to be Mounted Count", min_value=0, max_value=20, value=0)
                m_mounts_p = st.number_input("Mounts Performed", min_value=0, max_value=30, value=0)
                m_quality = st.selectbox("Quality Status", QUALITY_STATUSES, index=QUALITY_STATUSES.index("manually_entered") if "manually_entered" in QUALITY_STATUSES else 0)

            m_submit = st.form_submit_button("Insert Observation Record")
            if m_submit and m_obs_id.strip() and m_anim:
                rec_data = {
                    "observation_id": m_obs_id.strip(),
                    "animal_id": m_anim,
                    "timestamp": m_time,
                    "observation_interval_minutes": 120,
                    "activity_count": m_act,
                    "rumination_time_min": m_rum,
                    "body_temperature_c": m_temp,
                    "standing_to_be_mounted_count": m_stbm,
                    "mounts_performed": m_mounts_p,
                    "mounts_received": 0,
                    "data_source": "manual_entry",
                    "quality_status": m_quality,
                    "quality_notes": "Entered via UI"
                }
                success, msg = DatasetManager.add_record("sensor_observations", rec_data)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)
