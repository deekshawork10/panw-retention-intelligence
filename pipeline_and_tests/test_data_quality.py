import pytest
import pandas as pd
import os

# ==========================================
# FIX: Bulletproof File Paths
# Forces Python to look in the exact directory where this script lives.
# ==========================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

@pytest.fixture(scope="module")
def accounts_df():
    return pd.read_csv(os.path.join(CURRENT_DIR, 'accounts_data.csv'))

@pytest.fixture(scope="module")
def contracts_df():
    return pd.read_csv(os.path.join(CURRENT_DIR, 'contracts_data.csv'))

@pytest.fixture(scope="module")
def usage_df():
    return pd.read_csv(os.path.join(CURRENT_DIR, 'Daily_Usage_Logs.csv'))


# ==========================================
# TEST 1: The "Orphaned Usage" Hard Truth
# ==========================================
def test_no_orphaned_usage_logs(usage_df, accounts_df):
    """
    Presentation Slide 6: Orphaned Usage Quarantines.
    Ensures every account_id in the telemetry logs actually exists in the core Accounts table.
    """
    valid_accounts = set(accounts_df['account_id'].unique())
    usage_accounts = set(usage_df['account_id'].unique())
    
    orphans = usage_accounts - valid_accounts
    
    # The assertion: Zero rows/orphans means a clean pipeline
    assert len(orphans) == 0, f"PIPELINE FAILURE: Found orphaned usage logs for non-existent account IDs: {orphans}"


# ==========================================
# TEST 2: Contract Date Logic (Mid-Year Expansions Prep)
# ==========================================
def test_contracts_end_after_start(contracts_df):
    """
    Data Integrity: Ensure contract end dates logically occur after start dates 
    so the BigQuery gaps-and-islands window functions don't break.
    """
    start_dates = pd.to_datetime(contracts_df['start_date'])
    end_dates = pd.to_datetime(contracts_df['end_date'])
    
    invalid_dates = contracts_df[start_dates >= end_dates]
    assert len(invalid_dates) == 0, f"DATA ERROR: Found {len(invalid_dates)} contracts where end_date is on or before start_date."


# ==========================================
# TEST 3: Financial Integrity
# ==========================================
def test_no_negative_commit_dollars(contracts_df):
    """
    Data Integrity: Annual commit dollars cannot be negative.
    """
    negative_commits = contracts_df[contracts_df['annual_commit_dollars'] < 0]
    assert len(negative_commits) == 0, "DATA ERROR: Found contracts with negative annual commit dollars."


def test_no_negative_usage(usage_df):
    """
    Data Integrity: Compute credits consumed cannot be negative.
    """
    negative_usage = usage_df[usage_df['compute_credits_consumed'] < 0]
    assert len(negative_usage) == 0, "DATA ERROR: Found usage logs with negative compute credits consumed."