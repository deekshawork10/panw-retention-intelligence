-- =====================================================================
-- 02_data_quality_tests.sql
-- Engine: Google BigQuery (Standard SQL)
--
-- Convention: each test query returns ZERO rows when the data is clean.
-- Any returned rows = TEST FAILURE (dbt-style "test" semantics: the
-- rows returned ARE the offending records, ready for triage).
-- Run each statement independently, or wire them up as dbt singular
-- tests / BigQuery scheduled assertions.
-- =====================================================================


-- ---------------------------------------------------------------
-- TEST 1: Orphaned Usage
--   Usage logs pointing at an account_id that does not exist in
--   Accounts (referential integrity violation on the FK).
--   Expectation if clean: 0 rows.
-- ---------------------------------------------------------------
SELECT
    'orphaned_usage'            AS test_name,
    u.log_id,
    u.account_id                AS unknown_account_id,
    u.date,
    u.compute_credits_consumed
FROM `gcs_raw_data.Daily_Usage_Logs` u
LEFT JOIN `gcs_raw_data.Accounts` a
       ON u.account_id = a.account_id
WHERE a.account_id IS NULL
ORDER BY u.account_id, u.date;


-- ---------------------------------------------------------------
-- TEST 2: Rogue Usage (out-of-contract consumption)
--   Usage rows for KNOWN accounts where the usage date is not
--   covered by ANY contract window (start_date..end_date) for that
--   account — e.g., consumption months after the contract ended.
--   Known accounts only: pure orphans are already caught by Test 1,
--   keeping each test's failure signal independent.
--   Expectation if clean: 0 rows.
-- ---------------------------------------------------------------
SELECT
    'rogue_out_of_contract_usage'   AS test_name,
    u.log_id,
    u.account_id,
    u.date                          AS usage_date,
    u.compute_credits_consumed,
    (SELECT MAX(c2.end_date)
       FROM `gcs_raw_data.Contracts` c2
      WHERE c2.account_id = u.account_id)  AS latest_contract_end_date
FROM `gcs_raw_data.Daily_Usage_Logs` u
JOIN `gcs_raw_data.Accounts` a
  ON u.account_id = a.account_id
WHERE NOT EXISTS (
    SELECT 1
    FROM `gcs_raw_data.Contracts` c
    WHERE c.account_id = u.account_id
      AND u.date BETWEEN c.start_date AND c.end_date
)
ORDER BY u.account_id, u.date;


-- ---------------------------------------------------------------
-- TEST 3: Shelfware Check
--   Accounts holding an ACTIVE contract worth > $50,000 in annual
--   commit but with ZERO rows ever recorded in Daily_Usage_Logs.
--   "Active" = contract window covers the anchor date (2026-12-31).
--   Expectation if clean: 0 rows.
-- ---------------------------------------------------------------
SELECT
    'shelfware_zero_usage'                  AS test_name,
    a.account_id,
    a.company_name,
    COUNT(c.contract_id)                    AS active_contracts,
    SUM(c.annual_commit_dollars)            AS total_active_commit_dollars
FROM `gcs_raw_data.Accounts` a
JOIN `gcs_raw_data.Contracts` c
  ON a.account_id = c.account_id
WHERE DATE '2026-12-31' BETWEEN c.start_date AND c.end_date
  AND c.annual_commit_dollars > 50000
  AND NOT EXISTS (
      SELECT 1
      FROM `gcs_raw_data.Daily_Usage_Logs` u
      WHERE u.account_id = a.account_id
  )
GROUP BY a.account_id, a.company_name
ORDER BY total_active_commit_dollars DESC;
