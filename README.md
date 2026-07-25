# GCS Retention Intelligence: Activated ARR (aARR)

## Overview

This repository contains the end-to-end technical prototype for the Global Customer Services (GCS) "North Star" metric initiative. It supports the organization's transition from a traditional TCV/ARR model into a hybrid consumption-based business model. 

The core of this initiative is **Activated ARR (aARR)**—a unified health metric that bridges the gap between financial bookings, actual platform consumption, and technical health to accurately predict revenue retention.

## Methodology

This project was developed using a spec-driven, AI-first methodology. Using AI coding assistants (Cursor/Claude Code) paired with strict Markdown specifications, this project moved rapidly from concept to working prototype, demonstrating how to architect and implement complex data solutions efficiently.

## Repository Structure

* **/data_generation**

  Contains the Python scripts `Faker`, `pandas`) used to simulate 12 months of highly realistic, messy B2B SaaS data. This includes mathematically enforced edge cases such as "Spike & Drop" usage, "Shelfware" (zero usage), Consistent Overages, Mid-Year Expansions, and Orphaned Usage logs.

* **/specs**

  Contains the core product and technical specifications `aARR_metric_spec.md`). This document defines the aARR mathematical thresholds (the >50% rolling 90-day consumption gate) and explicit edge-case routing logic.

* **/pipeline_and_tests**

  Contains the dbt-style BigQuery SQL scripts for:

  1. Transforming the raw simulated data into a clean `account_health_scorecard`.

  2. Executing automated data quality assertions (e.g., quarantining orphaned usage and flagging shelfware anomalies).

* **/dashboard**

  Contains a lightweight, interactive HTML/CSS prototype `index.html`) demonstrating a dual-view UI:

  * **Executive Snapshot:** Locked quarterly financial reporting for leadership and compensation tracking.

  * **KPI Sentinel:** A rolling, operational view for CSMs featuring an agentic workflow that detects anomalies and drafts remediation plans.

## How to View the Prototype

To view the UI prototype, navigate to the `/dashboard` folder and open `index.html` in any modern web browser.