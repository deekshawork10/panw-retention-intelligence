import pandas as pd
import os

print("--- PHASE 1: SYNTHETIC DATA AUDIT ---")

# 1. Load the generated files
try:
    accounts = pd.read_csv('data_generation/Accounts.csv')
    contracts = pd.read_csv('data_generation/Contracts.csv')
    logs = pd.read_csv('data_generation/Daily_Usage_Logs.csv')
    print("✅ CSV files loaded successfully.\n")
except FileNotFoundError:
    print("❌ Error: Could not find CSV files. Ensure they are in the '/data_generation' folder.")
    exit()

# 2. Test for Shelfware (~10% of accounts with NO logs)
accounts_with_logs = logs['account_id'].unique()
shelfware_accounts = accounts[~accounts['account_id'].isin(accounts_with_logs)]
shelfware_pct = (len(shelfware_accounts) / len(accounts)) * 100
print(f"📊 Shelfware Test: Found {len(shelfware_accounts)} accounts with ZERO usage logs ({shelfware_pct:.1f}%).")
if 9.0 <= shelfware_pct <= 11.0:
    print("   ✅ Passed: Successfully matched the ~10% requirement.")
else:
    print("   ❌ Failed: AI missed the 10% target. Reprompt required.")

# 3. Test for Orphaned Usage (150 logs with non-existent account_ids)
valid_account_ids = accounts['account_id'].unique()
orphan_logs = logs[~logs['account_id'].isin(valid_account_ids)]
print(f"\n📊 Orphaned Usage Test: Found {len(orphan_logs)} orphaned log entries.")
if len(orphan_logs) >= 150:
    print("   ✅ Passed: System successfully generated rogue/orphaned usage.")
else:
    print("   ❌ Failed: Did not generate the requested 150 orphan rows.")

# 4. Test for Mid-Year Expansions (Multiple contracts per account)
multi_contract_accounts = contracts.groupby('account_id').size()
expanded_accounts = multi_contract_accounts[multi_contract_accounts > 1]
print(f"\n📊 Expansion Test: Found {len(expanded_accounts)} accounts with multiple active contracts.")
if len(expanded_accounts) > 10:
    print("   ✅ Passed: Mid-year expansion anomaly injected successfully.")
else:
    print("   ❌ Failed: Missing overlapping contracts.")

print("\n-------------------------------------------")
print("If all tests show ✅, your data is presentation-ready!")