-- =====================================================================
-- 01_aARR_pipeline.sql
-- Model: account_health_scorecard
-- Engine: Google BigQuery (Standard SQL)
--
-- Purpose:
--   Transform raw contract + usage data into an account-level scorecard
--   that reports Total Contracted ARR vs. "Activated ARR" (aARR):
--   ARR only counts as *activated* when the account actually consumed
--   >= 50% of its prorated included compute credits over the trailing
--   90 days ending at the anchor date.
--
-- dbt note:
--   In a dbt project, drop the CREATE OR REPLACE TABLE wrapper, set
--   {{ config(materialized='table') }}, and replace the hardcoded
--   `gcs_raw_data.*` references with {{ source('gcs_raw_data', '...') }}.
-- =====================================================================

CREATE OR REPLACE TABLE `gcs_raw_data.account_health_scorecard` AS

WITH

-- ---------------------------------------------------------------
-- STEP 0: Configuration (anchor date + trailing 90-day window)
--   window = [anchor - 89 days, anchor]  -> exactly 90 calendar days
-- ---------------------------------------------------------------
config AS (
    SELECT
        DATE '2026-12-31'                                  AS anchor_date,
        DATE_SUB(DATE '2026-12-31', INTERVAL 89 DAY)       AS window_start,
        90                                                 AS window_days
),

-- ---------------------------------------------------------------
-- STEP 1: Handle Mid-Year Expansions (overlapping contracts)
--   Classic "gaps and islands" merge using window functions:
--   1a. For each account, order contracts by start_date and compute
--       the running MAX(end_date) over all PRIOR contracts.
--   1b. A contract starts a NEW island only if its start_date is
--       AFTER every previous contract has ended (no overlap).
--       Overlapping contracts (expansions) share an island.
--   1c. Island id = running sum of "new island" flags.
-- ---------------------------------------------------------------
contracts_ordered AS (
    SELECT
        account_id,
        contract_id,
        start_date,
        end_date,
        annual_commit_dollars,
        included_monthly_compute_credits,
        MAX(end_date) OVER (
            PARTITION BY account_id
            ORDER BY start_date, end_date
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ) AS prev_running_max_end
    FROM `gcs_raw_data.Contracts`
),

island_flags AS (
    SELECT
        *,
        CASE
            WHEN prev_running_max_end IS NULL THEN 1          -- first contract
            WHEN start_date > prev_running_max_end THEN 1     -- gap => new island (e.g., clean renewal)
            ELSE 0                                            -- overlap => same island (expansion)
        END AS is_new_island
    FROM contracts_ordered
),

islands_assigned AS (
    SELECT
        *,
        SUM(is_new_island) OVER (
            PARTITION BY account_id
            ORDER BY start_date, end_date
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS island_id
    FROM island_flags
),

-- ---------------------------------------------------------------
-- STEP 2: Merge each island into ONE effective contract period.
--   Overlapping expansion contracts are merged: timeframes unioned,
--   dollars and credits SUMMED once per island (no double counting
--   of the same contract, and no dropping of the expansion uplift).
-- ---------------------------------------------------------------
merged_contracts AS (
    SELECT
        account_id,
        island_id,
        MIN(start_date)                          AS effective_start_date,
        MAX(end_date)                            AS effective_end_date,
        SUM(annual_commit_dollars)               AS total_commit_dollars,
        SUM(included_monthly_compute_credits)    AS total_monthly_credits,
        COUNT(*)                                 AS contracts_in_island
    FROM islands_assigned
    GROUP BY account_id, island_id
),

-- ---------------------------------------------------------------
-- STEP 3: Keep islands ACTIVE during the trailing 90-day window
--   and prorate included credits to the days the island actually
--   overlaps the window (handles mid-window churn correctly).
--   Daily credit rate = monthly credits * 12 / 365.
-- ---------------------------------------------------------------
active_contracts AS (
    SELECT
        m.account_id,
        m.total_commit_dollars,
        m.total_monthly_credits,
        DATE_DIFF(
            LEAST(m.effective_end_date, c.anchor_date),
            GREATEST(m.effective_start_date, c.window_start),
            DAY
        ) + 1 AS active_days_in_window
    FROM merged_contracts m
    CROSS JOIN config c
    WHERE m.effective_start_date <= c.anchor_date
      AND m.effective_end_date   >= c.window_start
),

account_contract_summary AS (
    SELECT
        account_id,
        SUM(total_commit_dollars) AS total_contracted_arr,
        SUM(
            total_monthly_credits * 12 / 365.0 * active_days_in_window
        ) AS prorated_included_credits_90d
    FROM active_contracts
    GROUP BY account_id
),

-- ---------------------------------------------------------------
-- STEP 4: Trailing 90-day compute consumption per account
-- ---------------------------------------------------------------
usage_90d AS (
    SELECT
        u.account_id,
        SUM(u.compute_credits_consumed) AS credits_consumed_90d
    FROM `gcs_raw_data.Daily_Usage_Logs` u
    CROSS JOIN config c
    WHERE u.date BETWEEN c.window_start AND c.anchor_date
    GROUP BY u.account_id
),

-- ---------------------------------------------------------------
-- STEP 5: Final scorecard
--   Activated_ARR = full contracted ARR if 90-day consumption
--   >= 50% of prorated included credits, else 0.
--   LEFT JOINs keep zero-usage (shelfware) accounts in the output
--   with Activated_ARR = 0 rather than silently dropping them.
-- ---------------------------------------------------------------
final AS (
    SELECT
        a.account_id,
        a.company_name,
        r.csm_id,
        r.name                                          AS name,        -- CSM name
        r.region,
        ROUND(COALESCE(s.total_contracted_arr, 0), 2)   AS Total_Contracted_ARR,
        ROUND(COALESCE(s.prorated_included_credits_90d, 0), 2)
                                                        AS prorated_included_credits_90d,
        ROUND(COALESCE(u.credits_consumed_90d, 0), 2)   AS credits_consumed_90d,
        CASE
            WHEN COALESCE(s.prorated_included_credits_90d, 0) > 0
                 AND COALESCE(u.credits_consumed_90d, 0)
                     >= 0.5 * s.prorated_included_credits_90d
            THEN ROUND(s.total_contracted_arr, 2)
            ELSE 0
        END                                             AS Activated_ARR
    FROM `gcs_raw_data.Accounts` a
    LEFT JOIN `gcs_raw_data.csm_rep` r
           ON a.rep_id = r.csm_id
    LEFT JOIN account_contract_summary s
           ON a.account_id = s.account_id
    LEFT JOIN usage_90d u
           ON a.account_id = u.account_id
)

SELECT *
FROM final;
