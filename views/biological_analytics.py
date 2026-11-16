"""
BOVISENSE Page: Biological Analytics, Scientific References & Ground-Truth Evaluation (Module 10)
Integrates herd-level statistical synthesis, independent academic ground-truth validation,
and verified scientific citations.
"""
import datetime
import io
import pandas as pd
import streamlit as st

from components.cards import render_disclaimer
from components.charts import plot_confusion_matrix
from config.references import SCIENTIFIC_REFERENCES
from database.db_manager import db
from database.repositories import GroundTruthRepository, PredictionRepository
from services.evaluation import EvaluationEngine


def show():
    st.title("📊 Biological Analytics & Educational Evaluation")
    st.caption("Herd statistical aggregation, independent ground-truth evaluation, and verified scientific references.")

    tab_eval, tab_analytics, tab_refs = st.tabs([
        "Independent Ground-Truth Evaluation", "Herd Biological Analytics", "Scientific Reference Registry"
    ])

    # TAB 1: INDEPENDENT GROUND-TRUTH EVALUATION
    with tab_eval:
        st.subheader("Independent Ground-Truth Evaluation Engine")
        render_disclaimer(
            "Evaluation matches independently stored gold-standard biological labels against algorithm predictions. "
            "Unknown ground-truth annotations are strictly excluded from binary evaluation and never assumed to be negative.",
            "info"
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            scenario = st.selectbox(
                "Evaluation Scenario / Event Type",
                ["estrus", "heat_stress", "fever_screening", "respiratory_screening", "mastitis_screening"]
            )
        with c2:
            threshold = st.slider("Prediction Decision Cutoff (Score)", min_value=30.0, max_value=90.0, value=60.0, step=5.0)
        with c3:
            tolerance = st.slider("Temporal Matching Window (Hours)", min_value=6, max_value=72, value=24, step=6)

        eval_engine = EvaluationEngine()
        result = eval_engine.evaluate_scenario(event_type=scenario, score_threshold=threshold, tolerance_hours=tolerance)

        if result["status"] == "unavailable":
            st.warning(f"⚠️ **Evaluation Notice**: {result['message']}")
            gt_count = db.get_row_count("educational_ground_truth")
            st.info(f"Total ground truth records currently in database: {gt_count}. (You can upload or restore ground truth in Dataset Management).")
        else:
            st.success(f"Evaluation completed for scenario: **{scenario.replace('_', ' ').title()}**")

            # Metrics Row
            m = result["metrics"]
            mc1, mc2, mc3, mc4 = st.columns(4)
            with mc1:
                st.metric("Accuracy", f"{m['accuracy']:.3f}" if m['accuracy'] is not None else "N/A")
            with mc2:
                st.metric("Precision (PPV)", f"{m['precision']:.3f}" if m['precision'] is not None else "N/A")
            with mc3:
                st.metric("Recall / Sensitivity", f"{m['recall_sensitivity']:.3f}" if m['recall_sensitivity'] is not None else "N/A")
            with mc4:
                st.metric("F1 Score", f"{m['f1_score']:.3f}" if m['f1_score'] is not None else "N/A")

            col_cm, col_summary = st.columns([1, 1])
            with col_cm:
                st.plotly_chart(plot_confusion_matrix(result["confusion_matrix"]), use_container_width=True)

            with col_summary:
                st.write("### Evaluation Breakdown")
                st.write(f"- **Total Gold Standard Annotations:** `{result['total_labels']}`")
                st.write(f"- **Evaluated Matching Cases:** `{result['evaluated_cases']}`")
                st.write(f"- **Unknown Labels Excluded:** `{result['unknown_labels_excluded']}`")
                st.write(f"- **Specificity (TNR):** `{m['specificity']}`")
                st.write(f"- **False Positive Rate:** `{m['false_positive_rate']}`")
                st.caption(result["scientific_note"])

    # TAB 2: HERD BIOLOGICAL ANALYTICS
    with tab_analytics:
        st.subheader("Herd Performance & Biological Trends")

        # Basic summaries
        tot_animals = db.get_row_count("animals")
        tot_sensors = db.get_row_count("sensor_observations")
        tot_env = db.get_row_count("environmental_observations")
        tot_milk = db.get_row_count("milk_records")

        st.write(f"Analytics synthesized from `{tot_animals}` animals, `{tot_sensors}` sensor logs, `{tot_env}` weather observations, and `{tot_milk}` milk records.")

        # Milk Yield by Breed
        breed_milk = db.fetchall("""
            SELECT a.breed, AVG(m.total_yield_l) as avg_yield, COUNT(m.milk_record_id) as rec_count
            FROM animals a JOIN milk_records m ON a.animal_id = m.animal_id
            GROUP BY a.breed
        """)
        if breed_milk:
            st.write("### Average Milk Yield by Breed")
            st.dataframe(pd.DataFrame(breed_milk), use_container_width=True)

        # Environmental THI distribution
        thi_dist = db.fetchall("""
            SELECT heat_stress_category, COUNT(*) as count 
            FROM environmental_observations 
            GROUP BY heat_stress_category
        """)
        if thi_dist:
            st.write("### Thermal Stress Exposure Hours")
            st.dataframe(pd.DataFrame(thi_dist), use_container_width=True)

    # TAB 3: SCIENTIFIC REFERENCES REGISTRY
    with tab_refs:
        st.subheader("Scientific References & Biological Rules Registry")
        st.caption("Documented empirical sources, population contexts, and prototype disclosures.")

        for ref in SCIENTIFIC_REFERENCES:
            with st.expander(f"{ref['reference_id']}: {ref['parameter']} ({ref['status']})"):
                st.write(f"**Formula / Threshold:** `{ref['formula_or_threshold']}`")
                st.write(f"**Source:** {ref['reference_source']} ({ref['publication_year']})")
                st.write(f"**Population Context:** {ref['population_context']}")
                st.write(f"**Units:** `{ref['measurement_units']}`")
                st.write(f"**Scientific Limitations:** {ref['limitations']}")
                st.caption(f"Config Version: {ref['configuration_version']} • Added: {ref['date_added']}")
