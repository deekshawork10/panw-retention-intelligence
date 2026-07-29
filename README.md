Markdown
# Palo Alto Networks: GCS Retention Intelligence

This repository contains the data generation scripts, pipeline logic, and visualization prototype for an agentic AI retention dashboard. It is designed to expose "shelfware" risk by cross-referencing quantitative product telemetry with qualitative CSM health scores.

## Repository Structure

├── /data_generation         # Scripts to generate the ~250k row synthetic dataset
├── /specs                   # Product Requirements and Technical logic (aARR_metric_spec.md)
├── /pipeline_and_tests      # Flask API engine, SQL models, and data quality unit tests
├── /dashboard               # HTML/JS Chart.js visualization prototype
└── Executive_Scorecard_Presentation.xlsx # Executive financial scorecard

---

## How to Run the Application Locally

**Prerequisites:** Python 3.9+ installed.

### 1. Install Dependencies
```bash
pip install pandas numpy flask flask-cors faker pytest
2. Generate the Synthetic Dataset
Run the data generator to create relational tables and inject controlled enterprise anomalies (shelfware, spikes, mid-year expansions, and orphaned logs):

Bash
python data_generation/generate_data.py
3. Run Data Pipeline Verification
Verify data integrity and test active quarantine gates:

Bash
cd pipeline_and_tests
python verify_data.py
4. Launch the Agentic Flask API
Start the backend server to serve metric payloads and AI remediation drafts:

Bash
python agent_api.py