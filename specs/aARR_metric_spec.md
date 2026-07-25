# Product Specification: Activated ARR (aARR)

## Executive Summary

As Palo Alto Networks (PANW) Global Customer Services (GCS) transitions toward a hybrid consumption-based model, traditional Annual Recurring Revenue (ARR) and Net Retention Rate (NRR) create operational blind spots. A customer may commit to a high annual dollar amount but fail to deploy or consume the platform, leading to sudden renewal churn.

**Activated ARR (aARR)** bridges financial bookings and actual platform consumption into a single health-aware metric.

---

## Metric Definition & Mathematical Logic

An account's total ARR is recognized as **Activated ARR (aARR)** only if the customer crosses a sustained consumption gate over a rolling 90-day evaluation window.

### Primary Activation Formula

$$\text{Activated ARR} = \begin{cases} \text{Contracted ARR}, & \text{if } \frac{\text{Consumption}_{90d}}{\text{Prorated Commit}_{90d}} \ge 0.50 \text{ AND } \text{Open Sev-1 Incidents} = 0 \\ 0, & \text{otherwise} \end{cases}$$

Where:

* **$\text{Consumption}_{90d}$**: Total compute credits consumed in `Daily_Usage_Logs` over the trailing 90 days.

* **$\text{Prorated Commit}_{90d}$**: $\left(\frac{\text{Included Monthly Compute Credits}}{30}\right) \times 90$

---

## Edge Case Handling & Routing Rules

| Edge Case Anomaly | System Behavior & Metric Impact | Operational Routing |

| :--- | :--- | :--- |

| **Shelfware** (0 usage logs) | `aARR = $0`. Full ARR flagged as "Unactivated Risk". | Automated alert assigned to CSM for immediate onboarding intervention. |

| **Spike & Drop** | Trailing 90-day window dampens single-day spikes. Transient bursts fail to activate the 90-day threshold. | Health score flagged with "Unsustained Burst". |

| **Mid-Year Expansion** | Overlapping contracts are merged. Timeframes combine, and total commit credits are aggregated. | Prorated baseline updates dynamically in BigQuery pipeline. |

| **Orphaned Usage** | Usage logs with non-existent `account_id`s are quarantined by Data Quality test assertions `02_data_quality_tests.sql`). | Quarantined in `stg_orphaned_usage` table for Analytics Engineering triage. |

---

## Governance & Dual-View Architecture

1. **Executive Snapshot (Finance/Leadership):** Locked quarterly reporting window. Changes to usage after quarter-close do not alter historical closed comp/churn snapshots.

2. **KPI Sentinel (CSM Operational View):** Live rolling 30/90-day evaluation. Triggers real-time AI remediation workflows for accounts dropping below the 50% activation line.