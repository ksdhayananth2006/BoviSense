"""
BOVISENSE Page: Farm Dashboard and Herd Management (Module 1)
All metrics and visualizations are dynamically derived from active database records.
"""
import datetime
import pandas as pd
import streamlit as st

from components.cards import render_metric_card, render_disclaimer, render_thi_badge, render_health_alert_badge
from components.charts import plot_herd_pie
from database.db_manager import db
from database.repositories import AnimalRepository, EnvironmentalRepository, HealthRepository, ReproductiveRepository


def show():
    st.title("🌾 Farm Dashboard & Herd Management")
    st.caption("Real-time operational summary computed directly from verified database records.")

    animal_repo = AnimalRepository()
    env_repo = EnvironmentalRepository()
    health_repo = HealthRepository()

    # Dynamic Herd Counts
    counts = animal_repo.count_summary()
    active_health_alerts = health_repo.get_active_alerts()
    recent_env = env_repo.get_recent(limit=1)
    
    # Calculate average milk yield over last 7 days
    milk_avg_row = db.fetchone("""
        SELECT AVG(total_yield_l) as avg_yield, COUNT(*) as rec_count 
        FROM milk_records 
        WHERE record_datetime >= date('now', '-7 days')
    """)
    avg_yield = round(milk_avg_row["avg_yield"], 1) if (milk_avg_row and milk_avg_row["avg_yield"]) else None
    yield_contrib_count = milk_avg_row["rec_count"] if milk_avg_row else 0

    # Recent calvings
    calvings_count = db.get_row_count("calving_records")

    # Metrics row 1
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        render_metric_card("Total Active Herd", str(counts["total"]), f"{counts['cows']} cows, {counts['bulls']} bulls, {counts['calves']} calves")
    with c2:
        render_metric_card("Lactating Cows", str(counts["lactating"]), "Active milking status")
    with c3:
        render_metric_card("Confirmed Pregnant", str(counts["pregnant"]), "Diagnosed pregnancies")
    with c4:
        render_metric_card("Active Health Alerts", str(len(active_health_alerts)), "Unresolved clinical screenings")
    with c5:
        yield_str = f"{avg_yield} L/day" if avg_yield is not None else "No 7d Data"
        render_metric_card("Avg 7d Milk Yield", yield_str, f"Based on {yield_contrib_count} records")

    st.markdown("---")

    # Current Environmental Condition
    st.subheader("Current Barn Environmental State")
    if recent_env:
        e = recent_env[0]
        col_e1, col_e2, col_e3, col_e4 = st.columns(4)
        with col_e1:
            st.metric("Barn Location", e.get("barn_id") or "General")
        with col_e2:
            st.metric("Ambient Temperature", f"{e['temperature_c']:.1f} °C")
        with col_e3:
            st.metric("Relative Humidity", f"{e['relative_humidity_pct']:.1f} %")
        with col_e4:
            st.write("**Thermal Stress Index**")
            render_thi_badge(e["thi_value"], e.get("heat_stress_category", "Low"))
    else:
        st.info("No environmental observations currently recorded in database.")

    st.markdown("---")

    # Layout: Charts and Alerts
    col_chart, col_alerts = st.columns([1, 1])

    with col_chart:
        st.subheader("Herd Demographic Distribution")
        if counts["total"] > 0:
            st.plotly_chart(plot_herd_pie(counts), use_container_width=True)
        else:
            st.info("No animals registered in database.")

    with col_alerts:
        st.subheader("Active Biological & Health Alerts")
        if active_health_alerts:
            for alt in active_health_alerts[:5]:
                with st.container():
                    render_health_alert_badge(alt["priority"], alt["alert_category"])
                    st.write(f"**Animal**: {alt['animal_id']} • **Date**: {alt['alert_datetime']}")
                    st.caption(f"Triggers: `{alt['triggering_parameters']}`")
                    st.divider()
        else:
            st.success("No active health screening alerts. Herd operating in nominal range.")

    st.markdown("---")

    # Recent Activity log
    st.subheader("Recent Calvings & Clinical Observations")
    c_calv, c_obs = st.columns(2)
    with c_calv:
        recent_calvings = db.fetchall("SELECT * FROM calving_records ORDER BY calving_datetime DESC LIMIT 5")
        st.write(f"**Recent Calvings ({calvings_count} total)**")
        if recent_calvings:
            st.dataframe(pd.DataFrame(recent_calvings)[["calving_id", "dam_id", "calving_datetime", "calving_outcome"]], use_container_width=True)
        else:
            st.caption("No calving records logged.")

    with c_obs:
        recent_obs = db.fetchall("SELECT * FROM health_observations ORDER BY observation_datetime DESC LIMIT 5")
        st.write(f"**Recent Clinical Observations ({len(recent_obs)} shown)**")
        if recent_obs:
            st.dataframe(pd.DataFrame(recent_obs)[["health_observation_id", "animal_id", "observation_datetime", "body_temperature_c"]], use_container_width=True)
        else:
            st.caption("No health observations recorded.")
