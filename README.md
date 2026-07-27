# Palo Alto Networks: GCS Retention Intelligence

This repository contains the data generation scripts, pipeline logic, and visualization prototype for an agentic AI retention dashboard. It is designed to expose "shelfware" risk by cross-referencing quantitative product telemetry with qualitative CSM health scores.

## Repository Structure

├── /data_generation       # Scripts to generate the ~250k row synthetic dataset
├── /specs                 # Product Requirements and Technical logic (aARR_metric_spec.md)
├── /pipeline_and_tests    # Flask API engine and data quality unit tests
├── /dashboard             # HTML/JS Chart.js visualization prototype
└── Executive_Deck.pdf     # The strategic presentation for the live interview


## How to Run the Application Locally

**Prerequisites:** You will need Python 3 installed. 

**1. Install Dependencies**
```bash
pip install pandas flask flask-cors