import pandas as pd
import random
from datetime import datetime, timedelta

print("⚙️ Generating perfectly aligned CSM and Account Health data...")

try:
    df_acc = pd.read_csv('accounts_data.csv')
    account_ids = df_acc['account_id'].tolist()
    print(f"✅ Linked to {len(account_ids)} existing accounts.")
except FileNotFoundError:
    print("❌ Could not find accounts_data.csv. Make sure you are in the right directory.")
    exit()

# 1. Generate the CSM Rep Data (~50 rows)
regions = ['AMER', 'EMEA', 'APAC']
segments = ['Enterprise', 'Mid-Market']
csm_data = []

for i in range(1, 51):
    csm_data.append({
        'csm_id': f'CSM_{i:03d}',
        'name': f'Rep Name {i}',
        'region': random.choice(regions),
        'segment': random.choice(segments)
    })

df_csm = pd.DataFrame(csm_data)
df_csm.to_csv('csm_rep_data.csv', index=False)
print("✅ Created csm_rep_data.csv (50 rows)")

# 2. Generate Account Health Data (~50,000 rows - Weekly Snapshots)
health_data = []
colors = ['Green', 'Yellow', 'Red']
start_date = datetime(2026, 1, 1)

print("⏳ Generating 52,000 weekly account health records...")

for acc in account_ids:
    for week in range(52):
        current_date = start_date + timedelta(days=week*7)
        health_data.append({
            'health_color': random.choices(colors, weights=[0.7, 0.2, 0.1])[0],
            'account_id': acc,
            'date': current_date.strftime('%Y-%m-%d'),
            # Adding the missing column specified in the image
            'compute_credits_consumed': random.randint(0, 500) 
        })

df_health = pd.DataFrame(health_data)
df_health.to_csv('account_health_data.csv', index=False)
print("✅ Created account_health_data.csv (52,000 rows)")
print("🚀 Done! Your data now perfectly matches the image specifications.")