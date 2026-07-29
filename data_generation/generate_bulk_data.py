import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import uuid

print("Initializing Bulk Data Generation (Target: ~200k logs)...")

# 1. Generate CSM_rep (~50 rows)
csm_data = {
    'csm_id': [f"CSM-{str(i).zfill(3)}" for i in range(1, 51)],
    'name': [f"Rep Name {i}" for i in range(1, 51)],
    'region': np.random.choice(['AMER', 'EMEA', 'APAC'], 50),
    'segment': np.random.choice(['Enterprise', 'Mid-Market'], 50)
}
df_csm = pd.DataFrame(csm_data)

# 2. Generate Accounts (~1,000 rows) + Inject our Edge Cases
account_ids = [f"ACC-{str(i).zfill(4)}" for i in range(1, 996)]
company_names = [f"Company {i} LLC" for i in range(1, 996)]

# INJECT EDGE CASES
edge_case_ids = ["ACC-EDGE-1", "ACC-EDGE-2", "ACC-EDGE-3", "ACC-EDGE-4", "ACC-EDGE-5"]
edge_case_names = ["Healthy Corp", "Spike Inc", "Ghost LLC", "Grow Corp", "Fresh Start"]

account_ids.extend(edge_case_ids)
company_names.extend(edge_case_names)

account_data = {
    'account_id': account_ids,
    'company_name': company_names,
    'industry': np.random.choice(['Finance', 'Healthcare', 'Tech', 'Retail', 'Manufacturing'], 1000),
    'rep_id': np.random.choice(df_csm['csm_id'], 1000)
}
df_accounts = pd.DataFrame(account_data)

# 3. Generate Contracts (~1,200 rows)
contract_data = []
base_date = datetime(2025, 1, 1)
eval_date = datetime(2026, 12, 31)

# Generate random contracts for the 995 normal accounts
for acc_id in account_ids[:-5]:
    start = base_date + timedelta(days=random.randint(0, 365))
    end = start + timedelta(days=365*2) # 2 year contracts
    arr = random.choice([50000, 120000, 240000, 300000, 500000])
    
    contract_data.append({
        'contract_id': f"CON-{uuid.uuid4().hex[:6].upper()}",
        'account_id': acc_id,
        'start_date': start.strftime('%Y-%m-%d'),
        'end_date': end.strftime('%Y-%m-%d'),
        'annual_commit_dollars': arr,
        'included_monthly_compute_credits': int(arr / 120)
    })

# Add ~200 random mid-year expansion contracts
for i in range(200):
    acc_id = random.choice(account_ids[:-5])
    start = base_date + timedelta(days=random.randint(180, 300))
    end = start + timedelta(days=365*2)
    contract_data.append({
        'contract_id': f"CON-EXP-{uuid.uuid4().hex[:6].upper()}",
        'account_id': acc_id,
        'start_date': start.strftime('%Y-%m-%d'),
        'end_date': end.strftime('%Y-%m-%d'),
        'annual_commit_dollars': 600000, 
        'included_monthly_compute_credits': 5000
    })

# INJECT EDGE CASE CONTRACTS
edge_contracts = [
    {"contract_id": "CON-EDGE-1", "account_id": "ACC-EDGE-1", "start_date": "2026-01-01", "end_date": "2026-12-31", "annual_commit_dollars": 120000, "included_monthly_compute_credits": 1000}, # Healthy Corp
    {"contract_id": "CON-EDGE-2", "account_id": "ACC-EDGE-2", "start_date": "2026-01-01", "end_date": "2026-12-31", "annual_commit_dollars": 120000, "included_monthly_compute_credits": 1000}, # Spike Inc
    {"contract_id": "CON-EDGE-3", "account_id": "ACC-EDGE-3", "start_date": "2026-06-01", "end_date": "2027-05-31", "annual_commit_dollars": 300000, "included_monthly_compute_credits": 2500}, # Ghost LLC
    {"contract_id": "CON-EDGE-4A", "account_id": "ACC-EDGE-4", "start_date": "2026-01-01", "end_date": "2026-08-31", "annual_commit_dollars": 120000, "included_monthly_compute_credits": 1000}, # Grow Corp Old
    {"contract_id": "CON-EDGE-4B", "account_id": "ACC-EDGE-4", "start_date": "2026-09-01", "end_date": "2027-08-31", "annual_commit_dollars": 240000, "included_monthly_compute_credits": 2000}, # Grow Corp New (Expansion)
    {"contract_id": "CON-EDGE-5", "account_id": "ACC-EDGE-5", "start_date": "2026-12-15", "end_date": "2027-12-14", "annual_commit_dollars": 500000, "included_monthly_compute_credits": 4000}, # Fresh Start (<45 days)
]
contract_data.extend(edge_contracts)
df_contracts = pd.DataFrame(contract_data)

# 4. Generate Daily_Usage_Logs (~200,000 rows)
print("Generating ~200,000 daily usage logs... (This takes a few seconds)")
log_data = []

# Generate normal logs for normal accounts
active_accounts = account_ids[:-5]
for i in range(365):
    current_date = datetime(2026, 1, 1) + timedelta(days=i)
    date_str = current_date.strftime('%Y-%m-%d')
    
    # Take a sample of accounts active on this day to reach ~200k total
    daily_active = random.sample(active_accounts, 550) 
    for acc_id in daily_active:
        log_data.append({
            'log_id': f"LOG-{uuid.uuid4().hex[:8]}",
            'account_id': acc_id,
            'date': date_str,
            'compute_credits_consumed': random.randint(20, 150)
        })

# INJECT EDGE CASE USAGE LOGS (Last 90 Days of 2026)
ninety_days_start = datetime(2026, 10, 2)
for i in range(90):
    current_date = ninety_days_start + timedelta(days=i)
    date_str = current_date.strftime('%Y-%m-%d')
    
    # Healthy Corp (Consistent Usage)
    log_data.append({'log_id': f"LOG-H-{i}", 'account_id': "ACC-EDGE-1", 'date': date_str, 'compute_credits_consumed': 31}) 
    
    # Spike Inc (Usage early in 90 days, then drops to 0)
    if i < 20:
        log_data.append({'log_id': f"LOG-S-{i}", 'account_id': "ACC-EDGE-2", 'date': date_str, 'compute_credits_consumed': 55})
        
    # Ghost LLC (Shelfware - No logs appended)
    
    # Grow Corp (Consistent usage on new contract tier)
    log_data.append({'log_id': f"LOG-G-{i}", 'account_id': "ACC-EDGE-4", 'date': date_str, 'compute_credits_consumed': 61})

# Fresh Start only gets logs starting Dec 15
for i in range(16):
    current_date = datetime(2026, 12, 15) + timedelta(days=i)
    log_data.append({'log_id': f"LOG-F-{i}", 'account_id': "ACC-EDGE-5", 'date': current_date.strftime('%Y-%m-%d'), 'compute_credits_consumed': 10})

df_logs = pd.DataFrame(log_data)

# Export to CSV (Fixed capitalization to Daily_Usage_Logs.csv)
print("\nExporting datasets to CSV...")
df_csm.to_csv('csm_rep_data.csv', index=False)
df_accounts.to_csv('accounts_data.csv', index=False)
df_contracts.to_csv('contracts_data.csv', index=False)
df_logs.to_csv('Daily_Usage_Logs.csv', index=False)

print(f"✅ Success! Generated {len(df_accounts)} Accounts, {len(df_contracts)} Contracts, and {len(df_logs)} Usage Logs.")