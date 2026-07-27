# Product & Technical Specifications

**Project:** GCS Retention Intelligence Dashboard  

**Role:** Principal Product Manager Candidate

## 1. Executive Summary

Standard SaaS retention metrics (NRR, DBNRR) are lagging indicators. By the time Net Revenue Retention drops, the customer has already churned. This product introduces an **agentic AI pipeline** and operational dashboard designed to transition Customer Success from reactive reporting to proactive intervention. It isolates unactivated recurring revenue and automates workflows to prevent churn before it impacts the bottom line.

## 2. Core Metrics & KPI Evaluation

To accurately evaluate product adoption and account health, we leverage the following metric hierarchy:

*   **Portfolio Contracted ARR:** The total annualized value of all active contracts as of a dynamic snapshot date.

*   **The North Star - Activated ARR (aARR):** Contracted revenue associated with accounts that have consumed ≥50% of their prorated 90-day compute credits. This is our leading indicator for future NRR.

*   **Unactivated Risk ARR:** Revenue falling below the 50% activation threshold, mathematically modeled as high churn risk.

*   **CSM Pulse (Qualitative):** Manual account health scores (Green, Yellow, Red) inputted by Customer Success Managers.

## 3. Agentic Workflow & Anomaly Detection

The pipeline acts as a Sentinel, constantly evaluating the quantitative `System Status` against the qualitative `CSM Pulse`. The AI Agent dynamically routes interventions based on specific anomaly patterns:

1.  **The "Watermelon" Account (Critical Data Discrepancy):** 

    *   *Trigger:* System Usage = 0% AND CSM Pulse = Green. 

    *   *Agent Action:* Triggers a Data Integrity Audit via RevOps. This catches "false positive" accounts that appear healthy to the CSM but are quietly churning.

2.  **Spike & Drop:**

    *   *Trigger:* Historical usage was high, but recent 90-day trailing usage dropped severely.

    *   *Agent Action:* Escalates directly to a Technical Account Manager (TAM) to review migration logs for technical blockers.

3.  **Shelfware:**

    *   *Trigger:* 0% utilization with a Red/Yellow CSM Pulse.

    *   *Agent Action:* Initiates a deployment audit workflow for the CSM.

## 4. Technical Data Pipeline

The backend is powered by a Python ETL engine `agent_api.py`) that joins five relational CSV datasets (~250,000 total rows) in real-time. It supports dynamic time-series querying, allowing leadership to roll the pipeline back to specific quarters (Q1-Q4) to view historical quarter-over-quarter trend data.