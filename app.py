"""
BOVISENSE: Intelligent Cattle Reproductive, Health and Environmental Monitoring System
Main Application Entrypoint
"""
import streamlit as st

# Must be the very first Streamlit command
st.set_page_config(
    page_title="BOVISENSE — Intelligent Cattle Monitoring",
    page_icon="🐄",
    layout="wide",
    initial_sidebar_state="expanded"
)

from components.sidebar import render_sidebar_header, render_sidebar_footer
from config.theme import CUSTOM_CSS
from views import (
    dashboard,
    animal_management,
    sensor_management,
    estrus_monitoring,
    environmental_monitoring,
    health_monitoring,
    reproductive_management,
    calf_monitoring,
    milk_bcs_monitoring,
    biological_analytics,
    dataset_management,
    data_dictionary,
)

# Apply accessible custom styling
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Render top branding in sidebar
render_sidebar_header()

# Define single native navigation menu with explicit, unique url_path attributes
pages = {
    "Biological Modules": [
        st.Page(dashboard.show, title="Farm Dashboard", icon="🌾", url_path="farm-dashboard", default=True),
        st.Page(animal_management.show, title="Animal Registration & Profiles", icon="🐄", url_path="animal-registration"),
        st.Page(sensor_management.show, title="Sensor Data Management", icon="📡", url_path="sensor-data"),
        st.Page(estrus_monitoring.show, title="Estrus Indication & Analytics", icon="🔬", url_path="estrus-monitoring"),
        st.Page(environmental_monitoring.show, title="Environmental Monitoring & THI", icon="🌡️", url_path="environmental-monitoring"),
        st.Page(health_monitoring.show, title="Cattle Health & Alerts", icon="🩺", url_path="health-monitoring"),
        st.Page(reproductive_management.show, title="Reproductive & AI Management", icon="🧬", url_path="reproductive-management"),
        st.Page(calf_monitoring.show, title="Newborn Calf & Growth Monitoring", icon="🐮", url_path="calf-monitoring"),
        st.Page(milk_bcs_monitoring.show, title="Milk Production & BCS", icon="🥛", url_path="milk-bcs-monitoring"),
        st.Page(biological_analytics.show, title="Biological Analytics & Evaluation", icon="📊", url_path="biological-analytics"),
    ],
    "Data & Administration": [
        st.Page(dataset_management.show, title="Dataset Management", icon="🗄️", url_path="dataset-management"),
        st.Page(data_dictionary.show, title="Biological Data Dictionary", icon="📖", url_path="data-dictionary"),
    ]
}

# Native Streamlit navigation: exactly ONE menu with unique routes, clean and functional
pg = st.navigation(pages)

# Render live database status at bottom of sidebar
render_sidebar_footer()

# Execute selected page
pg.run()
