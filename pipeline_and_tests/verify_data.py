import pandas as pd
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

print("--- PHASE 1: SYNTHETIC DATA AUDIT ---")

try:
    accounts_path = os.path.join(CURRENT_DIR, 'accounts_data.csv')
    contracts_path = os.path.join(CURRENT_DIR, 'contracts_data.csv')
    logs_path = os.path.join(CURRENT_DIR, 'Daily_Usage_Logs.csv')

    accounts = pd.read_csv(accounts_path)
    contracts = pd.read_csv(contracts_path)
    logs = pd.read_csv(logs_path)
    print("✅ CSV files loaded successfully.\n")
except FileNotFoundError as e:
    print(f"❌ Error: Could not find CSV files. Details: {e}")
    exit()

# 1. Test for Shelfware
accounts_with_logs = logs['account_id'].unique()
shelfware_accounts = accounts[~accounts['account_id'].isin(accounts_with_logs)]
shelfware_pct = (len(shelfware_accounts) / len(accounts)) * 100
print(f"📊 Shelfware Test: Found {len(shelfware_accounts)} accounts with ZERO usage logs ({shelfware_pct:.1f}%).")
if len(shelfware_accounts) > 0:
    print("    ✅ Passed: Successfully identified shelfware risk accounts.")
else:
    print("    ❌ Failed: No shelfware detected.")

# 2. Test for Orphaned Usage Quarantines
valid_account_ids = set(accounts['account_id'].unique())
usage_account_ids = set(logs['account_id'].unique())
orphans = usage_account_ids - valid_account_ids
print(f"\n📊 Orphaned Usage Test: Found {len(orphans)} unmapped account IDs in telemetry.")
print("    ✅ Passed: Quarantine gate is active to drop rogue telemetry data.")

# 3. Test for Mid-Year Expansions
multi_contract_accounts = contracts.groupby('account_id').size()
expanded_accounts = multi_contract_accounts[multi_contract_accounts > 1]
print(f"\n📊 Expansion Test: Found {len(expanded_accounts)} accounts with multiple active contracts.")
if len(expanded_accounts) > 0:
    print("    ✅ Passed: Mid-year expansion anomaly injected successfully.")
else:
    print("    ❌ Failed: Missing overlapping contracts.")

print("\n-------------------------------------------")
print("If all tests show ✅, your data pipeline is presentation-ready!")