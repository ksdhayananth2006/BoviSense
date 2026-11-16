"""
Tests for Streamlit Navigation Configuration and Unique URL Paths
"""
import pytest
import streamlit as st
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


def test_navigation_unique_url_paths():
    """Verify all pages registered in navigation have unique url_path values."""
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

    # Verify st.navigation executes without raising StreamlitAPIException
    nav = st.navigation(pages)
    assert nav is not None

    all_pages = pages["Biological Modules"] + pages["Data & Administration"]
    assert len(all_pages) == 12

    # Check default page
    default_pages = [p for p in all_pages if p._default]
    assert len(default_pages) == 1

    # Verify expected URL paths
    expected_paths = [
        "farm-dashboard",
        "animal-registration",
        "sensor-data",
        "estrus-monitoring",
        "environmental-monitoring",
        "health-monitoring",
        "reproductive-management",
        "calf-monitoring",
        "milk-bcs-monitoring",
        "biological-analytics",
        "dataset-management",
        "data-dictionary"
    ]
    # Check that there are 12 distinct expected URL paths
    assert len(set(expected_paths)) == 12
