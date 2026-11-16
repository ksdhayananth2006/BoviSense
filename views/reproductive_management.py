"""
BOVISENSE Page: Reproductive and Artificial Insemination Management (Module 7)
Service records, breeding window calculations, return-to-estrus projections,
pregnancy diagnosis history, and calving parturition logs.
"""
import datetime
import pandas as pd
import streamlit as st

from components.cards import render_disclaimer
from config.thresholds import REPRODUCTIVE_CONSTANTS
from database.db_manager import db
from database.repositories import ReproductiveRepository
from services.dataset_manager import DatasetManager
from services.reproductive_manager import ReproductiveManager


def show():
    st.title("🧬 Reproductive & AI Management")
    st.caption("Breeding schedules, artificial insemination lots, pregnancy examinations, and parturition records.")

    render_disclaimer(
        "Return-to-estrus and gestation due dates are biological estimates based on typical cattle physiological references "
        "(21-day cycle, 279-day gestation). Artificial insemination records do not imply confirmed pregnancy.",
        "info"
    )

    repro_repo = ReproductiveRepository()

    tab_calc, tab_ai, tab_preg, tab_calv = st.tabs(["Breeding Timeline Calculator", "AI Service Records", "Pregnancy Examinations", "Calving Records"])

    # TAB 1: BREEDING TIMELINE CALCULATOR
    with tab_calc:
        st.subheader("Biological Reproductive Calculator")
        c1, c2 = st.columns(2)
        with c1:
            st.write("### Estimated Return-to-Estrus Window")
            ref_service_date = st.date_input("Service / Insemination Date", value=datetime.date.today())
            cycle_len = st.number_input("Estrous Cycle Length (Days)", min_value=17, max_value=26, value=21)

            ret_info = ReproductiveManager.calculate_return_to_estrus(ref_service_date.isoformat(), cycle_len)
            st.success(f"**Expected Return Date:** `{ret_info['expected_return_date']}`")
            st.write(f"**Watch Window:** `{ret_info['window_start']}` to `{ret_info['window_end']}`")

        with c2:
            st.write("### Estimated Calving Due Date")
            ref_conception_date = st.date_input("Assumed Conception Date", value=datetime.date.today())
            gest_len = st.number_input("Gestation Reference (Days)", min_value=260, max_value=300, value=279)

            due_info = ReproductiveManager.estimate_calving_due_date(ref_conception_date.isoformat(), gest_len)
            st.success(f"**Projected Calving Due Date:** `{due_info['estimated_due_date']}`")
            st.write(f"**Expected Window:** `{due_info['due_window_start']}` to `{due_info['due_window_end']}`")
            st.caption(due_info["disclaimer"])

    # TAB 2: AI SERVICE RECORDS
    with tab_ai:
        st.subheader("Artificial Insemination (AI) Procedures")
        ai_records = repro_repo.get_ai_records()
        if ai_records:
            st.dataframe(pd.DataFrame(ai_records), use_container_width=True)
        else:
            st.info("No AI records currently on file.")

        with st.expander("Record New AI Service Procedure"):
            female_animals = db.fetchall("SELECT animal_id FROM animals WHERE sex = 'F' ORDER BY animal_id")
            bull_batches = db.fetchall("SELECT semen_batch_id, bull_id FROM semen_batches WHERE batch_status = 'available'")

            with st.form("new_ai_form"):
                aic1, aic2, aic3 = st.columns(3)
                with aic1:
                    ai_id = st.text_input("AI Record ID *", f"AI-{datetime.datetime.now().strftime('%H%M%S')}")
                    ai_animal = st.selectbox("Female Animal *", [f["animal_id"] for f in female_animals] if female_animals else [""])
                    ai_time = st.text_input("AI Datetime", datetime.datetime.now().isoformat())
                with aic2:
                    ai_batch = st.selectbox("Semen Batch", [b["semen_batch_id"] for b in bull_batches] if bull_batches else ["LOT-2025-HF-09"])
                    ai_bull = st.text_input("Semen Bull ID", "BULL-001")
                    ai_tech = st.text_input("Technician / Inseminator", "Dr. Anil Sharma")
                with aic3:
                    ai_attempt = st.number_input("Attempt Number", min_value=1, max_value=10, value=1)
                    ai_method = st.selectbox("Method", ["frozen_semen_straw", "sexed_semen", "natural_service"])
                    ai_remarks = st.text_area("Remarks", "Deposited in uterine body.")

                ai_submit = st.form_submit_button("Save Insemination Record")
                if ai_submit and ai_id.strip() and ai_animal:
                    repro_repo.insert_ai_record({
                        "ai_id": ai_id.strip(),
                        "animal_id": ai_animal,
                        "event_id": None,
                        "ai_datetime": ai_time,
                        "semen_bull_id": ai_bull,
                        "semen_batch_id": ai_batch,
                        "technician": ai_tech,
                        "ai_attempt_number": int(ai_attempt),
                        "ai_type": ai_method,
                        "conception_method": "AI" if "semen" in ai_method else "natural_service",
                        "outcome_status": "pending",
                        "remarks": ai_remarks
                    })
                    st.success(f"AI record {ai_id} registered!")
                    st.rerun()

    # TAB 3: PREGNANCY EXAMINATIONS
    with tab_preg:
        st.subheader("Veterinary Pregnancy Diagnosis Records")
        preg_records = repro_repo.get_pregnancies()
        if preg_records:
            st.dataframe(pd.DataFrame(preg_records), use_container_width=True)
        else:
            st.info("No pregnancy examinations recorded.")

        with st.expander("Log Pregnancy Diagnosis Examination"):
            with st.form("new_preg_form"):
                pc1, pc2, pc3 = st.columns(3)
                with pc1:
                    p_id = st.text_input("Pregnancy Record ID *", f"PRG-{datetime.datetime.now().strftime('%H%M%S')}")
                    p_animal = st.selectbox("Animal ID *", [f["animal_id"] for f in female_animals] if female_animals else [""])
                    p_date = st.date_input("Examination Date", datetime.date.today())
                with pc2:
                    p_method = st.selectbox("Examination Method", ["transrectal_ultrasonography", "rectal_palpation", "blood_pregnancy_protein_b", "milk_pregnancy_test"])
                    p_status = st.selectbox("Pregnancy Status", ["confirmed_pregnant", "open_not_pregnant", "suspect_recheck", "pregnancy_loss"])
                    p_days = st.number_input("Estimated Days Pregnant", min_value=0, max_value=300, value=60)
                with pc3:
                    p_vet = st.text_input("Veterinarian ID", "Dr. Verma")
                    p_notes = st.text_area("Notes", "Viable embryo observed.")

                p_submit = st.form_submit_button("Record Diagnosis")
                if p_submit and p_id.strip() and p_animal:
                    # Calculate due date estimate if pregnant
                    due_date = None
                    conception_dt = None
                    if p_status == "confirmed_pregnant" and p_days > 0:
                        c_date = datetime.date.today() - datetime.timedelta(days=int(p_days))
                        conception_dt = c_date.isoformat()
                        due_date = (c_date + datetime.timedelta(days=279)).isoformat()

                    repro_repo.insert_pregnancy_record({
                        "pregnancy_id": p_id.strip(),
                        "animal_id": p_animal,
                        "ai_id": None,
                        "examination_date": p_date.isoformat(),
                        "examination_method": p_method,
                        "pregnancy_status": p_status,
                        "estimated_days_pregnant": int(p_days),
                        "estimated_due_date": due_date,
                        "conception_date": conception_dt,
                        "conception_date_status": "estimated",
                        "veterinarian_id": p_vet,
                        "notes": p_notes
                    })
                    # Update animal reproductive status
                    if p_status == "confirmed_pregnant":
                        db.execute("UPDATE animals SET reproductive_status = 'pregnant' WHERE animal_id = ?", (p_animal,))
                    st.success(f"Pregnancy diagnosis logged as {p_id}!")
                    st.rerun()

    # TAB 4: CALVING RECORDS
    with tab_calv:
        st.subheader("Calving Parturition Logs")
        calvings = repro_repo.get_calvings()
        if calvings:
            st.dataframe(pd.DataFrame(calvings), use_container_width=True)
        else:
            st.info("No calving events logged.")
