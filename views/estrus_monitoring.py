"""
BOVISENSE Page: Estrus Indication and Reproductive Analytics (Module 4)
Configurable multi-parameter biological scoring, individual baseline comparisons,
evidence coverage metrics, and explicit distinction between prediction and confirmation.
"""
import datetime
import json
import pandas as pd
import streamlit as st

from components.cards import render_disclaimer
from config.thresholds import DEFAULT_ESTRUS_WEIGHTS, ESTRUS_SCORE_BANDS, MIN_EVIDENCE_COVERAGE
from database.db_manager import db
from database.repositories import AnimalRepository, PredictionRepository, ReproductiveRepository, SensorRepository
from services.baseline_calculator import BaselineCalculator
from services.estrus_predictor import EstrusPredictor
from services.thi_calculator import THICalculator


def show():
    st.title("🔬 Estrus Indication & Reproductive Analytics")
    st.caption("Individual animal baseline deviation analysis, evidence coverage estimation, and breeding window alerts.")

    render_disclaimer(
        "Estrus scores reflect rule-based behavioral deviations relative to individual baselines and are configurable prototype indicators, "
        "not diagnostic probabilities. Unconfirmed algorithm predictions do not constitute confirmed reproductive events.",
        "warning"
    )

    pred_repo = PredictionRepository()
    sensor_repo = SensorRepository()
    repro_repo = ReproductiveRepository()

    tab_eval, tab_history, tab_weights = st.tabs(["Analyze Animal Estrus Status", "Prediction History & Review", "Scoring Weights Configuration"])

    # TAB 1: ANALYZE ANIMAL ESTRUS STATUS
    with tab_eval:
        st.subheader("Individual Estrus Deviation Assessment")

        c1, c2 = st.columns(2)
        with c1:
            cows = db.fetchall("SELECT animal_id, breed, reproductive_status FROM animals WHERE sex = 'F' ORDER BY animal_id")
            cow_ids = [c["animal_id"] for c in cows]
            selected_cow = st.selectbox("Select Female Animal", cow_ids if cow_ids else ["None"])
        with c2:
            window_days = st.slider("Baseline Window (Days)", min_value=7, max_value=28, value=14, step=7)

        if selected_cow and selected_cow != "None":
            # Fetch observations for this animal
            obs_list = sensor_repo.get_observations(selected_cow)
            if not obs_list:
                st.info(f"No sensor observations available for {selected_cow} to analyze.")
            else:
                # Latest observation
                latest_obs = obs_list[-1]
                st.write(f"**Latest Telemetry Timestamp:** `{latest_obs['timestamp']}`")

                # Baseline status
                act_base = BaselineCalculator.compute_animal_baseline(obs_list, "activity_count", window_days, latest_obs["timestamp"])
                rum_base = BaselineCalculator.compute_animal_baseline(obs_list, "rumination_time_min", window_days, latest_obs["timestamp"])

                col_b1, col_b2, col_b3 = st.columns(3)
                with col_b1:
                    st.metric("Baseline Valid Days", str(act_base["distinct_days"]), f"Target: >= 3 days ({act_base['status']})")
                with col_b2:
                    mean_str = f"{act_base['stats']['mean']} counts" if act_base["stats"] else "N/A"
                    st.metric("Baseline Activity Mean", mean_str, f"Std: {act_base['stats']['std'] if act_base['stats'] else 'N/A'}")
                with col_b3:
                    rum_str = f"{rum_base['stats']['mean']} min" if rum_base["stats"] else "N/A"
                    st.metric("Baseline Rumination Mean", rum_str, f"Std: {rum_base['stats']['std'] if rum_base['stats'] else 'N/A'}")

                # Contextual THI for barn
                cow_row = db.fetchone("SELECT barn_id FROM animals WHERE animal_id = ?", (selected_cow,))
                barn_id = cow_row.get("barn_id") if cow_row else None
                latest_env = db.fetchone("SELECT thi_value FROM environmental_observations WHERE barn_id = ? ORDER BY timestamp DESC LIMIT 1", (barn_id,))
                thi_val = float(latest_env["thi_value"]) if latest_env and latest_env["thi_value"] else None

                # Run Prediction Engine
                predictor = EstrusPredictor(weights=st.session_state.get("custom_estrus_weights", DEFAULT_ESTRUS_WEIGHTS))
                result = predictor.evaluate_observation(latest_obs, obs_list, thi_context=thi_val)

                st.markdown("---")
                st.subheader("Biological Indicator Score")

                if result["status"] == "insufficient_data":
                    st.warning(f"⚠️ **Insufficient Evidence**: {result['message']}")
                else:
                    sc1, sc2, sc3 = st.columns(3)
                    with sc1:
                        st.metric("Composite Estrus Score", f"{result['score']} / 100", f"Category: {result['confidence_category']}")
                    with sc2:
                        st.metric("Evidence Coverage", f"{int(result['coverage']*100)} %", "Weighted telemetry completeness")
                    with sc3:
                        st.write("**Recommended Action**")
                        st.info(result["action_recommendation"])

                    if result.get("thi_note"):
                        st.warning(f"🌡️ **Environmental Interaction**: {result['thi_note']}")

                    # Breakdown of contributing factors
                    with st.expander("🔍 View Parameter Contribution Breakdown"):
                        st.json(result["contributing_parameters"])

                    # Save prediction button
                    if st.button("💾 Persist Prediction to Record Registry", key=f"save_pred_{selected_cow}"):
                        saved = predictor.predict_and_store(latest_obs, obs_list, thi_context=thi_val)
                        st.success(f"Prediction saved with ID: {saved.get('prediction_id')}")

    # TAB 2: PREDICTION HISTORY & MANUAL CONFIRMATION
    with tab_history:
        st.subheader("Historical Estrus Predictions")
        preds = pred_repo.get_predictions(pred_type="estrus_indication")
        if preds:
            pdf = pd.DataFrame(preds)
            cols_show = ["prediction_id", "animal_id", "prediction_datetime", "prediction_score", "data_coverage", "confidence_category", "review_status"]
            st.dataframe(pdf[cols_show], use_container_width=True)

            st.markdown("---")
            st.subheader("Manual Review & Confirmation")
            st.caption("Convert an algorithm prediction into a confirmed biological reproductive event after visual or veterinary verification.")
            
            p_to_confirm = st.selectbox("Select Prediction ID to Review", [p["prediction_id"] for p in preds])
            p_rec = next((p for p in preds if p["prediction_id"] == p_to_confirm), None)

            if p_rec:
                st.write(f"**Target Animal:** {p_rec['animal_id']} • **Score:** {p_rec['prediction_score']} ({p_rec['confidence_category']})")
                with st.form("confirm_estrus_form"):
                    cf1, cf2 = st.columns(2)
                    with cf1:
                        c_officer = st.text_input("Confirmed By (Technician / Herdsman)", "Rajiv Kumar")
                        c_notes = st.text_area("Visual Examination Notes", "Standing heat confirmed; clear vaginal mucus discharge observed.")
                    with cf2:
                        c_status = st.selectbox("Confirmation Decision", ["confirmed", "suspected", "false_positive_rejected"])
                        c_time = st.text_input("Confirmation Datetime", datetime.datetime.now().isoformat())

                    c_submit = st.form_submit_button("Submit Review Decision")
                    if c_submit and p_rec:
                        evt_id = f"EVT-CONF-{datetime.datetime.now().strftime('%H%M%S')}"
                        repro_repo.insert_event({
                            "event_id": evt_id,
                            "animal_id": p_rec["animal_id"],
                            "event_datetime": p_rec["prediction_datetime"],
                            "event_type": "confirmed_estrus" if c_status == "confirmed" else "suspected_estrus",
                            "event_source": "algorithm_with_visual_confirmation",
                            "observation_notes": c_notes,
                            "confirmation_status": c_status,
                            "confirmed_by": c_officer,
                            "confirmation_datetime": c_time,
                            "linked_prediction_id": p_rec["prediction_id"]
                        })
                        # Update prediction review status
                        db.execute(
                            "UPDATE prediction_results SET review_status = ? WHERE prediction_id = ?",
                            (f"reviewed_{c_status}", p_rec["prediction_id"])
                        )
                        st.success(f"Event recorded successfully as {evt_id}! Prediction status updated.")
                        st.rerun()
        else:
            st.info("No prediction records currently stored.")

    # TAB 3: CONFIGURATION OF WEIGHTS
    with tab_weights:
        st.subheader("Configurable Estrus Scoring Weights")
        st.caption("Adjust relative biological indicator weights. Configured weights must sum to exactly 100%.")

        current_weights = st.session_state.get("custom_estrus_weights", DEFAULT_ESTRUS_WEIGHTS.copy())

        with st.form("weights_form"):
            w1, w2 = st.columns(2)
            with w1:
                nw_act = st.slider("Activity Increase Weight (%)", 0, 50, int(current_weights.get("activity_increase", 0.25)*100))
                nw_std = st.slider("Standing Time Weight (%)", 0, 40, int(current_weights.get("standing_time", 0.15)*100))
                nw_stbm = st.slider("Standing to be Mounted Weight (%)", 0, 40, int(current_weights.get("standing_to_be_mounted", 0.15)*100))
                nw_mount = st.slider("Mounting Behaviour Weight (%)", 0, 40, int(current_weights.get("mounting_behavior", 0.15)*100))
            with w2:
                nw_rum = st.slider("Rumination Decrease Weight (%)", 0, 40, int(current_weights.get("rumination_decrease", 0.15)*100))
                nw_ly = st.slider("Lying Time Weight (%)", 0, 20, int(current_weights.get("lying_time", 0.05)*100))
                nw_temp = st.slider("Temperature Change Weight (%)", 0, 20, int(current_weights.get("temperature_change", 0.05)*100))
                nw_other = st.slider("Other Observations Weight (%)", 0, 20, int(current_weights.get("other_observations", 0.05)*100))

            total_w = nw_act + nw_std + nw_stbm + nw_mount + nw_rum + nw_ly + nw_temp + nw_other
            st.write(f"**Total Weight Sum:** `{total_w}%` (Target: 100%)")

            w_save = st.form_submit_button("Save Weights Configuration")
            if w_save:
                if total_w != 100:
                    st.error(f"Weights must sum to exactly 100%. Current sum: {total_w}%.")
                else:
                    st.session_state["custom_estrus_weights"] = {
                        "activity_increase": nw_act / 100.0,
                        "standing_time": nw_std / 100.0,
                        "standing_to_be_mounted": nw_stbm / 100.0,
                        "mounting_behavior": nw_mount / 100.0,
                        "rumination_decrease": nw_rum / 100.0,
                        "lying_time": nw_ly / 100.0,
                        "temperature_change": nw_temp / 100.0,
                        "other_observations": nw_other / 100.0
                    }
                    st.success("Scoring weights updated successfully!")
