"""
BOVISENSE Page: Formal Biological Data Dictionary (Part 6.1)
Comprehensive educational reference covering all primary biological datasets and telemetry variables.
"""
import pandas as pd
import streamlit as st

from config.settings import PRIMARY_DATASETS
from services.data_dictionary_data import DATA_DICTIONARY
from services.data_validator import DATASET_SCHEMAS


def show():
    st.title("📖 Biological Data Dictionary")
    st.caption("Standardized metadata definitions, physiological interpretations, measurement units, and validation rules for academic biotechnology monitoring.")

    sel_dataset = st.selectbox("Select Target Biological Dataset", PRIMARY_DATASETS)

    schema = DATASET_SCHEMAS.get(sel_dataset, {})
    dict_entries = DATA_DICTIONARY.get(sel_dataset, [])

    st.subheader(f"Dataset: `{sel_dataset}`")
    st.write(f"- **Primary Key:** `{schema.get('primary_key', 'id')}`")
    st.write(f"- **Total Defined Schema Columns:** `{len(schema.get('columns', []))}`")
    st.write(f"- **Mandatory Fields:** `{', '.join(schema.get('required', []))}`")

    st.markdown("---")

    if dict_entries:
        for entry in dict_entries:
            with st.expander(f"📌 Column: {entry['column']} ({entry['type']}) — Required: {entry['required']}"):
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**Description:** {entry['description']}")
                    st.write(f"**Measurement Unit:** `{entry['unit']}`")
                    st.write(f"**Permitted Values:** {entry['permitted']}")
                    st.write(f"**Validation Rule:** {entry['rule']}")
                    st.write(f"**Example Value:** `{entry['example']}`")
                with c2:
                    st.info(f"**Biological & Physiological Interpretation:**\n\n{entry['interpretation']}")
    else:
        # Fallback table from schema
        st.write("### Schema Field List")
        cols_summary = []
        for col in schema.get("columns", []):
            is_req = "Yes" if col in schema.get("required", []) else "No"
            col_type = schema.get("types", {}).get(col, str).__name__
            cols_summary.append({
                "Column Name": col,
                "Data Type": col_type,
                "Required": is_req,
                "Permitted Values": str(schema.get("enums", {}).get(col, "Any valid " + col_type))
            })
        st.dataframe(pd.DataFrame(cols_summary), use_container_width=True)
