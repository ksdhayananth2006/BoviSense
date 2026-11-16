"""
BOVISENSE Page: Milk Production and Body Condition Monitoring (Module 9)
Milking session aggregation without double-counting, somatic cell count surveillance,
and longitudinal 1.0 to 5.0 Body Condition Scoring (BCS).
"""
import datetime
import pandas as pd
import streamlit as st

from components.cards import render_disclaimer
from components.charts import plot_milk_trends
from config.thresholds import BCS_LIMITS
from database.db_manager import db
from database.repositories import MilkAndBCSRepository
from services.dataset_manager import DatasetManager
from services.milk_analyzer import MilkAnalyzer


def show():
    st.title("🥛 Milk Production & Body Condition (BCS)")
    st.caption("Lactation performance tracking, milking session aggregation, SCC monitoring, and 5-point BCS evaluation.")

    render_disclaimer(
        "Somatic cell count (SCC) and session milk yield reductions provide preliminary subclinical indicators. "
        "Mastitis must not be diagnosed from milk yield or SCC alone.",
        "warning"
    )

    milk_repo = MilkAndBCSRepository()

    tab_milk, tab_bcs, tab_log_milk, tab_log_bcs = st.tabs([
        "Herd Milk Performance", "BCS Evaluation", "Log Milking Session", "Log BCS Assessment"
    ])

    # TAB 1: HERD MILK PERFORMANCE
    with tab_milk:
        st.subheader("Milk Yield & Quality Trends")
        cows = db.fetchall("SELECT animal_id FROM animals WHERE sex = 'F' ORDER BY animal_id")
        cow_ids = [c["animal_id"] for c in cows]

        sel_cow = st.selectbox("Filter by Cow", ["All Herd"] + cow_ids)

        if sel_cow == "All Herd":
            all_milk = db.fetchall("SELECT * FROM milk_records ORDER BY record_datetime DESC LIMIT 500")
        else:
            all_milk = milk_repo.get_milk_records(sel_cow)

        if all_milk:
            daily_df = MilkAnalyzer.aggregate_daily_yields(all_milk)
            st.plotly_chart(plot_milk_trends(daily_df), use_container_width=True)

            with st.expander("View Daily Aggregated Yield Table"):
                st.dataframe(daily_df, use_container_width=True)
        else:
            st.info("No milk records available.")

    # TAB 2: BCS EVALUATION
    with tab_bcs:
        st.subheader("Body Condition Scoring (1.0 to 5.0 Scale)")
        st.caption("Ferguson et al. (1994) standard 5-point scale in 0.25 point increments.")

        bcs_all = db.fetchall("SELECT * FROM bcs_records ORDER BY assessment_date DESC LIMIT 100")
        if bcs_all:
            st.dataframe(pd.DataFrame(bcs_all), use_container_width=True)
        else:
            st.info("No BCS assessments logged.")

    # TAB 3: LOG MILKING SESSION
    with tab_log_milk:
        st.subheader("Log Milking Session Record")
        with st.form("new_milking_form"):
            mc1, mc2, mc3 = st.columns(3)
            with mc1:
                m_id = st.text_input("Milk Record ID *", f"MILK-{datetime.datetime.now().strftime('%H%M%S')}")
                m_cow = st.selectbox("Animal ID *", cow_ids if cow_ids else [""])
                m_time = st.text_input("Record Datetime", datetime.datetime.now().isoformat())
            with mc2:
                m_session = st.selectbox("Milking Session *", ["morning", "evening", "afternoon", "daily_total"])
                m_type = st.selectbox("Record Type *", ["session", "daily_total"])
                m_yield = st.number_input("Yield (Liters) *", min_value=0.0, max_value=60.0, value=14.5, step=0.1)
            with mc3:
                m_scc = st.number_input("Somatic Cell Count (cells/mL)", min_value=0.0, max_value=5000000.0, value=140000.0, step=10000.0)
                m_cond = st.number_input("Electrical Conductivity (mS/cm)", min_value=0.0, max_value=15.0, value=5.2, step=0.1)
                m_app = st.selectbox("Milk Appearance", ["normal", "clots", "watery", "blood_tinged", "discolored"])

            m_remarks = st.text_area("Remarks", "Routine parlor reading.")
            m_submit = st.form_submit_button("Save Milking Record")

            if m_submit and m_id.strip() and m_cow:
                DatasetManager.add_record("milk_records", {
                    "milk_record_id": m_id.strip(),
                    "animal_id": m_cow,
                    "record_datetime": m_time,
                    "milking_session": m_session,
                    "record_type": m_type,
                    "morning_yield_l": m_yield if m_session == "morning" else None,
                    "evening_yield_l": m_yield if m_session == "evening" else None,
                    "total_yield_l": m_yield,
                    "milk_conductivity": m_cond,
                    "somatic_cell_count": m_scc,
                    "milk_appearance": m_app,
                    "data_source": "parlor_meter",
                    "remarks": m_remarks
                })
                st.success(f"Milking record {m_id} saved!")
                st.rerun()

    # TAB 4: LOG BCS ASSESSMENT
    with tab_log_bcs:
        st.subheader("Log Body Condition Score Assessment")
        with st.form("new_bcs_form"):
            bc1, bc2 = st.columns(2)
            with bc1:
                b_id = st.text_input("BCS Record ID *", f"BCS-{datetime.datetime.now().strftime('%H%M%S')}")
                b_cow = st.selectbox("Target Cow ID *", cow_ids if cow_ids else [""])
                b_date = st.date_input("Assessment Date", datetime.date.today())
                b_val = st.slider("BCS Value (1.0 to 5.0) *", min_value=1.0, max_value=5.0, value=3.0, step=0.25)
            with bc2:
                b_assessor = st.text_input("Assessor", "Dr. Sharma")
                b_stage = st.selectbox("Lactation Stage", ["early_lactation", "mid_lactation", "late_lactation", "dry_period", "transition"])
                b_wt = st.number_input("Recorded Body Weight (kg)", min_value=200.0, max_value=1200.0, value=580.0, step=1.0)
                b_notes = st.text_area("Assessment Notes", "Palpation of transverse processes and pins.")

            b_submit = st.form_submit_button("Save BCS Record")
            if b_submit and b_id.strip() and b_cow:
                DatasetManager.add_record("bcs_records", {
                    "bcs_record_id": b_id.strip(),
                    "animal_id": b_cow,
                    "assessment_date": b_date.isoformat(),
                    "bcs_value": b_val,
                    "assessor": b_assessor,
                    "assessment_method": "visual_palpation",
                    "lactation_stage": b_stage,
                    "body_weight_kg": b_wt,
                    "remarks": b_notes
                })
                st.success(f"BCS record {b_id} saved for {b_cow}!")
                st.rerun()
