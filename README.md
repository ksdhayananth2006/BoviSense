# BOVISENSE
### Intelligent Cattle Reproductive, Health and Environmental Monitoring System

An academic biotechnology application for precision livestock monitoring, biological data management, rule-based clinical screening, and independent ground-truth evaluation.

---

## Key Features

- **Farm Dashboard & Herd Management**: Dynamic summary counts, lactating herd tracking, active clinical alerts, recent calvings, and environmental status.
- **Animal Registration & Profiles**: Pedigree associations, longitudinal weights, sensor telemetry, reproductive history, and clinical logs.
- **Sensor Data Management**: Multi-metric time-series visualizations (activity, rumination, body temperature), quality audits, and manual telemetry entry.
- **Estrus Indication & Analytics**: Rolling individual animal baseline comparisons (7/14/28 days), configurable prototype weights, evidence coverage requirements, and review/confirmation workflows.
- **Environmental Monitoring & THI**: Ambient dry-bulb temperature, relative humidity, NRC (1971) Temperature-Humidity Index calculation, and heat stress categorization.
- **Cattle Health Surveillance & Alerts**: Pyrexia (fever) screening (adult vs calf thresholds), mastitis screening, respiratory surveillance, alert deduplication, and veterinary resolution notes.
- **Reproductive & AI Management**: 21-day estrous cycle return estimation, 279-day gestation calving due date projections, AI records, and pregnancy tracking.
- **Newborn Calf & Growth Monitoring**: Average Daily Gain (ADG) calculations, colostrum optical/digital Brix refractometry evaluations, and neonatal care logs.
- **Milk Production & Body Condition**: Milking session yield aggregation without double counting, SCC surveillance, and 5-point Ferguson Body Condition Scoring.
- **Biological Analytics & Evaluation**: Independent ground-truth evaluation engine, confusion matrix heatmaps, classification performance metrics (sensitivity, specificity, F1), and scientific references registry.
- **Complete Dataset Management**: Full control over all 13 primary biological CSV datasets (including `educational_ground_truth.csv`), atomic transactional imports with rollback on error, formula injection sanitization, pre-destructive backups, and sample data restoration.

---

## Technology Stack

- **Language:** Python 3.11+
- **Application Framework:** Streamlit
- **Persistent Database:** SQLite (Foreign keys & Write-Ahead Logging active)
- **Data Manipulation:** Pandas & NumPy
- **Statistical Calculations:** SciPy & NumPy
- **Interactive Visualizations:** Plotly
- **Testing:** Pytest

---

## Installation & Setup

1. **Activate Virtual Environment**:
   ```bash
   .venv\Scripts\activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Automated Test Suite**:
   ```bash
   pytest -v
   ```

4. **Launch Streamlit Application**:
   ```bash
   streamlit run app.py
   ```

---

## 13 Primary Biological Datasets

1. `animals.csv`
2. `sensor_observations.csv`
3. `environmental_observations.csv`
4. `reproductive_events.csv`
5. `ai_records.csv`
6. `pregnancy_records.csv`
7. `calving_records.csv`
8. `health_observations.csv`
9. `health_alerts.csv`
10. `milk_records.csv`
11. `bcs_records.csv`
12. `calf_care_records.csv`
13. `educational_ground_truth.csv`

---

## Documentation

A complete, 15-section technical report is available in:
[reports/technical_report.md](file:///d:/Studies/PY/BoviSense%20New/reports/technical_report.md)
