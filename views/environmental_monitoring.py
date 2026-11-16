"""
BOVISENSE Page: Environmental Monitoring and THI (Module 5)
Calculates Temperature-Humidity Index (THI), evaluates thermal stress categories,
and tracks barn-level and animal-level bioclimatic exposure history.
"""
import datetime
import pandas as pd
import streamlit as st

from components.cards import render_disclaimer, render_thi_badge
from components.charts import plot_environmental_thi
from config.thresholds import THI_BANDS
from database.db_manager import db
from database.repositories import EnvironmentalRepository
from services.dataset_manager import DatasetManager
from services.thi_calculator import THICalculator


def show():
    st.title("🌡️ Environmental Monitoring & THI")
    st.caption("Barn microclimate telemetry, Temperature-Humidity Index calculation, and heat stress categorization.")

    env_repo = EnvironmentalRepository()

    tab_overview, tab_history, tab_entry = st.tabs(["Barn Environmental Status", "Historical Exposure Trends", "Log Environmental Record"])

    # TAB 1: BARN ENVIRONMENTAL STATUS
    with tab_overview:
        st.subheader("Current Barn Climatic State")
        barns = db.fetchall("SELECT * FROM barns WHERE status = 'active' ORDER BY barn_id")

        if barns:
            for b in barns:
                bid = b["barn_id"]
                latest_obs = env_repo.get_recent(barn_id=bid, limit=1)
                with st.container():
                    st.write(f"### 📍 {b['barn_name']} ({bid})")
                    st.caption(f"Location: {b.get('location')} • Capacity: {b.get('capacity')} animals")
                    if latest_obs:
                        obs = latest_obs[0]
                        c1, c2, c3, c4 = st.columns(4)
                        with c1:
                            st.metric("Temperature", f"{obs['temperature_c']} °C")
                        with c2:
                            st.metric("Relative Humidity", f"{obs['relative_humidity_pct']} %")
                        with c3:
                            st.metric("THI Value", f"{obs['thi_value']}")
                        with c4:
                            st.write("**Stress Level**")
                            render_thi_badge(obs["thi_value"], obs.get("heat_stress_category", "Low"))
                        st.caption(f"Last updated: {obs['timestamp']}")
                    else:
                        st.info("No recent environmental observations logged for this barn.")
                    st.divider()
        else:
            st.info("No active barns configured.")

    # TAB 2: HISTORICAL EXPOSURE TRENDS
    with tab_history:
        st.subheader("Climatic Trends & Exposure Analytics")
        c1, c2 = st.columns(2)
        with c1:
            barn_ids = [b["barn_id"] for b in barns]
            sel_barn = st.selectbox("Filter by Barn", ["All"] + barn_ids)
        with c2:
            limit_history = st.selectbox("Records Count", [100, 250, 500, 1000], index=1)

        history_records = env_repo.get_recent(barn_id=sel_barn if sel_barn != "All" else None, limit=limit_history)
        if history_records:
            hdf = pd.DataFrame(history_records)
            st.plotly_chart(plot_environmental_thi(hdf), use_container_width=True)

            with st.expander("View Raw Microclimate Logs Table"):
                st.dataframe(hdf, use_container_width=True)
        else:
            st.info("No environmental records found for selected criteria.")

    # TAB 3: LOG OBSERVATION
    with tab_entry:
        st.subheader("Log Barn Environmental Reading")
        with st.form("env_reading_form"):
            ec1, ec2, ec3 = st.columns(3)
            with ec1:
                e_id = st.text_input("Environment ID *", f"ENV-{datetime.datetime.now().strftime('%H%M%S')}")
                e_barn = st.selectbox("Barn *", barn_ids if barn_ids else ["BARN-A"])
                e_time = st.text_input("Timestamp", datetime.datetime.now().isoformat())
            with ec2:
                e_temp = st.number_input("Dry Bulb Temp (°C) *", min_value=-20.0, max_value=60.0, value=28.5, step=0.1)
                e_rh = st.number_input("Relative Humidity (%) *", min_value=0.0, max_value=100.0, value=70.0, step=0.5)
            with ec3:
                e_wind = st.number_input("Wind Speed (m/s)", min_value=0.0, max_value=50.0, value=1.2, step=0.1)
                e_solar = st.number_input("Solar Radiation (W/m²)", min_value=0.0, max_value=1500.0, value=250.0, step=10.0)

            e_submit = st.form_submit_button("Compute THI & Save Record")
            if e_submit and e_id.strip():
                # Compute THI
                calculated_thi = THICalculator.calculate_thi(e_temp, e_rh)
                category, _ = THICalculator.classify_thi(calculated_thi)

                new_env = {
                    "environment_id": e_id.strip(),
                    "barn_id": e_barn,
                    "timestamp": e_time,
                    "temperature_c": e_temp,
                    "relative_humidity_pct": e_rh,
                    "wind_speed_ms": e_wind,
                    "solar_radiation_wm2": e_solar,
                    "thi_value": calculated_thi,
                    "thi_formula_version": "1.0",
                    "heat_stress_category": category,
                    "data_source": "manual_weather_log",
                    "quality_status": "valid"
                }
                success, msg = DatasetManager.add_record("environmental_observations", new_env)
                if success:
                    st.success(f"Record logged! Calculated THI: {calculated_thi} ({category} Stress)")
                else:
                    st.error(msg)
