"""
BOVISENSE Page: Complete Dataset Management (Part 5)
Provides full administrative control over all 13 primary biological datasets,
including CSV upload, manual insertion, editing, deletion, clearing, export,
sample restoration, and import provenance history.
"""
import datetime
import io
import pandas as pd
import streamlit as st

from components.cards import render_disclaimer
from config.settings import PRIMARY_DATASETS
from database.backup_manager import backup_manager
from database.db_manager import db
from services.csv_importer import CSVImporter
from services.dataset_manager import DatasetManager
from services.data_validator import DATASET_SCHEMAS


def show():
    st.title("🗄️ Complete Dataset Management")
    st.caption("Administrative interface for uploading, browsing, editing, replacing, clearing, exporting, and restoring all 13 primary biological datasets.")

    tab_summary, tab_browse, tab_import, tab_export, tab_history, tab_backups = st.tabs([
        "Datasets Overview", "Browse & Edit Records", "Import CSV", "Export & Restore", "Import History", "Database Backups"
    ])

    # TAB 1: OVERVIEW
    with tab_summary:
        st.subheader("Biological Datasets Catalog")
        summary_list = DatasetManager.list_datasets()
        st.dataframe(pd.DataFrame(summary_list), use_container_width=True)

        st.markdown("---")
        st.write("### Quick Global Operations")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔄 Restore All Sample Datasets", help="Restores default sample data across all 13 datasets in relational order."):
                res = DatasetManager.restore_all_samples()
                st.success("All sample datasets restored successfully!")
                st.rerun()
        with c2:
            if st.button("💾 Create Database Backup Now"):
                p = backup_manager.create_backup("manual_checkpoint")
                st.success(f"Backup created: {p.name}")

    # TAB 2: BROWSE & EDIT RECORDS
    with tab_browse:
        st.subheader("Browse, Edit and Delete Records")
        sel_ds = st.selectbox("Select Target Dataset", PRIMARY_DATASETS)

        search_q = st.text_input(f"Search within '{sel_ds}'", "")
        records, total_count = DatasetManager.get_records(sel_ds, search_query=search_q, limit=100)

        st.caption(f"Displaying up to 100 of {total_count} matching records.")

        if records:
            rdf = pd.DataFrame(records)
            st.dataframe(rdf, use_container_width=True)

            st.markdown("---")
            st.write("### Record Operations")
            schema = DATASET_SCHEMAS[sel_ds]
            pk_col = schema["primary_key"]
            pk_list = [str(r[pk_col]) for r in records]

            col_del1, col_del2 = st.columns(2)
            with col_del1:
                st.write("**Delete Individual Record**")
                sel_pk = st.selectbox(f"Select Record by {pk_col}", pk_list)
                if st.button(f"Delete Record {sel_pk}", key=f"btn_del_rec_{sel_ds}"):
                    success, msg = DatasetManager.delete_record(sel_ds, sel_pk)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

            with col_del2:
                st.write("**Clear Complete Dataset Contents**")
                st.warning(f"Removes all records from '{sel_ds}' while preserving the table schema and audit log. Creates safety backup.")
                confirm_clear = st.checkbox(f"Confirm clearing all records from {sel_ds}", key=f"chk_clear_{sel_ds}")
                if st.button(f"Clear All Records in {sel_ds}", key=f"btn_clear_ds_{sel_ds}", disabled=not confirm_clear):
                    success, msg = DatasetManager.clear_dataset(sel_ds)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
        else:
            st.info(f"Dataset '{sel_ds}' is currently empty.")
            if sel_ds == "educational_ground_truth":
                st.caption("When ground truth is empty, the application functions normally; evaluation modules report ground truth as unavailable.")

    # TAB 3: IMPORT CSV
    with tab_import:
        st.subheader("Upload and Import CSV")
        st.caption("Transactions are strictly enforced. Conflicting or invalid files are rolled back without partial database corruption.")

        target_ds = st.selectbox("Target Dataset for Import", PRIMARY_DATASETS, key="import_target_ds")
        policy = st.selectbox("Import Policy", ["Append", "Update existing", "Replace", "Skip duplicates", "Reject duplicates"])

        uploaded_file = st.file_uploader(f"Select CSV file for '{target_ds}'", type=["csv"])

        if uploaded_file is not None:
            content = uploaded_file.getvalue()
            # Inspect file pre-flight
            inspect_info = CSVImporter.inspect_file(content, target_ds, uploaded_file.name)

            st.write("### Pre-Import Pre-Flight Summary")
            st.write(f"- **Filename:** `{inspect_info['filename']}`")
            st.write(f"- **Total Rows Found:** `{inspect_info['row_count']}`")
            st.write(f"- **Primary Key Present ({inspect_info['primary_key']}):** `{inspect_info['has_primary_key']}`")

            if inspect_info["missing_required"]:
                st.error(f"Missing required columns: {inspect_info['missing_required']}")
            else:
                st.success("All required columns detected in uploaded file.")

            st.write("**File Preview:**")
            st.dataframe(inspect_info["preview_df"], use_container_width=True)

            if not inspect_info["missing_required"]:
                if st.button("Execute Transactional Import", key="btn_exec_import"):
                    res = CSVImporter.execute_import(
                        file_content=content,
                        dataset_name=target_ds,
                        import_policy=policy,
                        filename=uploaded_file.name
                    )
                    if res["success"]:
                        st.success(f"Import successful! {res['message']}")
                        st.rerun()
                    else:
                        st.error(f"Import failed: {res['message']}")
                        if res.get("rejection_reasons"):
                            st.write("**Rejection Details:**")
                            for r in res["rejection_reasons"][:10]:
                                st.write(f"- {r}")

    # TAB 4: EXPORT & RESTORE
    with tab_export:
        st.subheader("Export & Single Dataset Restore")
        exp_ds = st.selectbox("Select Dataset to Export or Restore", PRIMARY_DATASETS, key="exp_ds_select")

        c_exp, c_res = st.columns(2)
        with c_exp:
            st.write("### Export to CSV")
            st.caption("Includes CSV formula injection sanitization protection.")
            csv_str = DatasetManager.export_csv(exp_ds)
            st.download_button(
                label=f"📥 Download {exp_ds}.csv",
                data=csv_str,
                file_name=f"{exp_ds}.csv",
                mime="text/csv"
            )

        with c_res:
            st.write("### Restore Sample Dataset")
            st.caption(f"Restores original verified sample data for '{exp_ds}'.")
            if st.button(f"Restore Sample {exp_ds}", key=f"restore_btn_{exp_ds}"):
                success, msg = DatasetManager.restore_sample_dataset(exp_ds)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    # TAB 5: IMPORT PROVENANCE HISTORY
    with tab_history:
        st.subheader("Import Provenance & Audit Logs")
        batches = db.fetchall("SELECT * FROM import_batches ORDER BY import_datetime DESC LIMIT 50")
        if batches:
            st.dataframe(pd.DataFrame(batches), use_container_width=True)
        else:
            st.info("No import batches recorded.")

        st.markdown("---")
        st.write("### Recent System Audit Logs")
        audits = db.fetchall("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 50")
        if audits:
            st.dataframe(pd.DataFrame(audits), use_container_width=True)

    # TAB 6: DATABASE BACKUPS
    with tab_backups:
        st.subheader("Database Backups & Point-in-Time Restore")
        st.caption("Live SQLite online backups preserving Write-Ahead Logging (WAL) state.")

        backups = backup_manager.list_backups()
        if backups:
            st.dataframe(pd.DataFrame(backups), use_container_width=True)

            b_files = [b["filename"] for b in backups]
            sel_b = st.selectbox("Select Backup to Restore", b_files)
            target_path = next((b["filepath"] for b in backups if b["filename"] == sel_b), None)

            st.warning("Restoring will replace current live database with the selected backup snapshot.")
            confirm_rst = st.checkbox("Confirm database restoration from backup", key="chk_db_restore")
            if st.button("Restore Database Snapshot", disabled=not confirm_rst):
                if target_path:
                    try:
                        backup_manager.restore_backup(target_path)
                        st.success("Database snapshot restored successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Restore failed: {e}")
        else:
            st.info("No existing database backups found.")
