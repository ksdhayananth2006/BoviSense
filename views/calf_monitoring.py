"""
BOVISENSE Page: Newborn Calf and Growth Monitoring (Module 8)
Neonatal care records, colostrum Brix refractometry, weight trajectory, and Average Daily Gain (ADG).
"""
import datetime
import pandas as pd
import streamlit as st

from components.cards import render_disclaimer
from database.db_manager import db
from services.calf_monitor import CalfMonitor
from services.dataset_manager import DatasetManager


def show():
    st.title("🐮 Newborn Calf & Growth Monitoring")
    st.caption("Neonatal management, colostrum quality (Brix %), vaccination records, and growth analytics.")

    tab_calves, tab_adg, tab_care = st.tabs(["Calf Roster", "ADG & Growth Trajectory", "Log Neonatal Care Record"])

    # TAB 1: CALF ROSTER
    with tab_calves:
        st.subheader("Active Youngstock & Replacement Heifers")
        calves = db.fetchall("""
            SELECT animal_id, animal_name, sex, breed, dob, dam_id, sire_id, birth_weight_kg, current_weight_kg, barn_id 
            FROM animals WHERE animal_type = 'calf' ORDER BY dob DESC
        """)
        if calves:
            st.dataframe(pd.DataFrame(calves), use_container_width=True)
        else:
            st.info("No calves registered in the database.")

    # TAB 2: ADG CALCULATOR
    with tab_adg:
        st.subheader("Average Daily Gain (ADG) Calculation")
        st.caption("Calculates body weight accretion rate over verified observation intervals.")

        c1, c2 = st.columns(2)
        with c1:
            calf_list = [c["animal_id"] for c in calves]
            sel_calf = st.selectbox("Select Calf", calf_list if calf_list else ["None"])
            w1 = st.number_input("Previous / Birth Weight (kg)", min_value=10.0, max_value=250.0, value=38.0, step=0.5)
            w2 = st.number_input("Current Weight (kg)", min_value=10.0, max_value=350.0, value=65.0, step=0.5)
            days = st.number_input("Days Between Measurements", min_value=1, max_value=365, value=35)

            if st.button("Calculate ADG"):
                adg = CalfMonitor.calculate_adg(w1, w2, days)
                if adg is not None:
                    st.success(f"**Average Daily Gain:** `{adg} kg/day` ({int(adg*1000)} g/day)")
                    if adg >= 0.7:
                        st.info("Growth rate meets dairy replacement standard (>= 700 g/day).")
                    else:
                        st.warning("Growth rate is below target (< 700 g/day); evaluate nutritional density.")
                else:
                    st.error("Invalid measurements or negative interval.")

        with c2:
            st.write("### Colostrum Quality Evaluation (Brix %)")
            st.caption("Optical / Digital Brix Refractometry indicates Immunoglobulin G (IgG) concentration.")
            brix_val = st.slider("Colostrum Brix Reading (%)", min_value=10.0, max_value=32.0, value=23.5, step=0.5)
            eval_res = CalfMonitor.evaluate_colostrum_brix(brix_val)

            st.write(f"**Quality Status:** `{eval_res['status']}`")
            st.write(f"**Classification:** {eval_res['quality']}")
            st.write(f"**Management Action:** {eval_res['action']}")

    # TAB 3: LOG NEONATAL CARE RECORD
    with tab_care:
        st.subheader("Log Calf Care Event")
        care_records = db.fetchall("SELECT * FROM calf_care_records ORDER BY event_datetime DESC LIMIT 50")
        if care_records:
            st.write(f"**Recent Care Events ({len(care_records)})**")
            st.dataframe(pd.DataFrame(care_records), use_container_width=True)

        with st.expander("Register New Care Event (Colostrum, Vaccination, Navel Care)"):
            with st.form("new_calf_care_form"):
                cc1, cc2 = st.columns(2)
                with cc1:
                    care_id = st.text_input("Care Record ID *", f"CARE-{datetime.datetime.now().strftime('%H%M%S')}")
                    care_calf = st.selectbox("Calf ID *", calf_list if calf_list else [""])
                    care_time = st.text_input("Datetime", datetime.datetime.now().isoformat())
                    care_type = st.selectbox("Care Event Type *", ["colostrum_feeding", "navel_antisepsis", "vaccination", "deworming", "weaning"])
                with cc2:
                    care_qty = st.number_input("Quantity", min_value=0.0, max_value=100.0, value=3.5, step=0.1)
                    care_unit = st.text_input("Quantity Unit", "liters")
                    care_brix = st.number_input("Colostrum Brix % (If Colostrum)", min_value=0.0, max_value=40.0, value=24.0, step=0.5)
                    care_by = st.text_input("Administered By", "Meena Patel")

                care_notes = st.text_area("Notes", "Colostrum fed within 2 hours of birth.")
                care_submit = st.form_submit_button("Save Care Record")

                if care_submit and care_id.strip() and care_calf:
                    DatasetManager.add_record("calf_care_records", {
                        "care_record_id": care_id.strip(),
                        "animal_id": care_calf,
                        "event_datetime": care_time,
                        "care_type": care_type,
                        "quantity": care_qty,
                        "quantity_unit": care_unit,
                        "colostrum_brix_pct": care_brix if care_type == "colostrum_feeding" else None,
                        "vaccination_name": None,
                        "medication_name": None,
                        "administered_by": care_by,
                        "notes": care_notes
                    })
                    st.success(f"Care event logged for {care_calf}!")
                    st.rerun()
