"""
B2B SaaS Synthetic Dataset Generator
=====================================
Generates 12 months (Jan 1 - Dec 31, 2026) of realistic B2B SaaS data
across 5 relational tables, with 5 mathematically-enforced anomalies:

  1. Spike & Drop      -> 5% of accounts burn 90% of annual credits in Month 1
  2. Shelfware         -> 10% of accounts pay a lot, log ZERO usage
  3. Consistent Overage-> 15% of accounts consume 120-150% of monthly credits, every month
  4. Mid-Year Expansion-> ~50 accounts get a 2nd overlapping contract starting in June
  5. Orphaned/Rogue    -> 150 logs with non-existent account_ids + 50 post-contract logs

Output: 5 CSV files in ./data_generation/
"""

import os
import random
import string
from datetime import date, timedelta

import numpy as np
import pandas as pd
from faker import Faker

# ---------------------------------------------------------------------------
# STEP 0: Reproducibility & constants
# ---------------------------------------------------------------------------
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
fake = Faker()
Faker.seed(SEED)

OUTPUT_DIR = "/data_generation"
YEAR_START = date(2026, 1, 1)
YEAR_END = date(2026, 12, 31)

N_CSMS = 50
N_ACCOUNTS = 1_000

REGIONS = ["AMER", "EMEA", "APAC", "LATAM"]
SEGMENTS = ["Enterprise", "Mid-Market"]
INDUSTRIES = [
    "Financial Services", "Healthcare", "Retail & E-Commerce", "Manufacturing",
    "Media & Entertainment", "Telecommunications", "Logistics & Supply Chain",
    "Energy & Utilities", "Public Sector", "Software & Technology",
    "Insurance", "Travel & Hospitality",
]
COMPANY_SUFFIXES = [
    "Inc.", "LLC", "Corp.", "Holdings", "Group", "Technologies",
    "Systems", "Labs", "Solutions", "Global", "Partners", "Industries",
]

def month_days(year: int, month: int):
    """Return a list of date objects for every day in a given month."""
    d = date(year, month, 1)
    days = []
    while d.month == month:
        days.append(d)
        d += timedelta(days=1)
    return days

ALL_MONTHS = list(range(1, 13))

# ---------------------------------------------------------------------------
# STEP 1: CSM_rep table (~50 rows)
# ---------------------------------------------------------------------------
csm_rows = []
for i in range(1, N_CSMS + 1):
    csm_rows.append({
        "csm_id": f"CSM-{i:03d}",
        "name": fake.name(),
        "region": random.choice(REGIONS),
        "segment": random.choice(SEGMENTS),
    })
df_csm = pd.DataFrame(csm_rows)

# ---------------------------------------------------------------------------
# STEP 2: Accounts table (~1,000 rows)
# ---------------------------------------------------------------------------
def make_company_name() -> str:
    """Professional-looking B2B company name, deduplicated by caller."""
    style = random.random()
    if style < 0.45:
        base = fake.company().split(",")[0].split(" and ")[0]
        return f"{base} {random.choice(COMPANY_SUFFIXES)}"
    elif style < 0.75:
        return f"{fake.last_name()}{random.choice(['Soft', 'Data', 'Cloud', 'Logic', 'Works', 'Metrics', 'Stack', 'Flow'])} {random.choice(COMPANY_SUFFIXES)}"
    else:
        return f"{fake.color_name().capitalize()} {random.choice(['Peak', 'Harbor', 'Summit', 'Bridge', 'Forge', 'Grid'])} {random.choice(COMPANY_SUFFIXES)}"

company_names = set()
while len(company_names) < N_ACCOUNTS:
    company_names.add(make_company_name())
company_names = sorted(company_names)
random.shuffle(company_names)

account_rows = []
for i in range(1, N_ACCOUNTS + 1):
    account_rows.append({
        "account_id": f"ACC-{i:05d}",
        "company_name": company_names[i - 1],
        "industry": random.choice(INDUSTRIES),
        "rep_id": random.choice(df_csm["csm_id"].tolist()),  # FK -> CSM_rep
    })
df_accounts = pd.DataFrame(account_rows)
all_account_ids = df_accounts["account_id"].tolist()

# ---------------------------------------------------------------------------
# STEP 3: Assign anomaly cohorts (DISJOINT sets, mathematically enforced)
# ---------------------------------------------------------------------------
shuffled = all_account_ids.copy()
random.shuffle(shuffled)

n_spike = int(N_ACCOUNTS * 0.05)      # 50
n_shelf = int(N_ACCOUNTS * 0.10)      # 100
n_over  = int(N_ACCOUNTS * 0.15)      # 150
n_expand = 50

spike_accounts   = set(shuffled[:n_spike])
shelf_accounts   = set(shuffled[n_spike:n_spike + n_shelf])
overage_accounts = set(shuffled[n_spike + n_shelf:n_spike + n_shelf + n_over])
normal_accounts  = [a for a in all_account_ids
                    if a not in spike_accounts | shelf_accounts | overage_accounts]

# Expansions drawn from normal accounts so anomalies stay cleanly separable
expansion_accounts = set(random.sample(normal_accounts, n_expand))

# ~5% of normal accounts churn early (contract ends mid-year) so that
# "usage after contract end" (Edge Case 5b) is possible within/near 2026
churned_accounts = set(random.sample(
    [a for a in normal_accounts if a not in expansion_accounts], 50))

# ---------------------------------------------------------------------------
# STEP 4: Contracts table (~1,200 rows)
#   1,000 primary + ~150 renewals + 50 mid-year expansions = ~1,200
# ---------------------------------------------------------------------------
contract_rows = []
contract_counter = 0

def next_contract_id() -> str:
    global contract_counter
    contract_counter += 1
    return f"CTR-{contract_counter:05d}"

# Credit tiers loosely tied to commit size (credits are a monthly allowance)
def commit_and_credits(is_shelfware: bool):
    if is_shelfware:
        # Edge Case 2: shelfware pays top-of-market
        annual = round(random.uniform(250_000, 900_000), 2)
    else:
        annual = round(np.random.lognormal(mean=11.2, sigma=0.7), 2)
        annual = float(min(max(annual, 15_000), 1_200_000))
    monthly_credits = int(annual / 12 * random.uniform(0.8, 1.2) / 10) * 10
    return annual, max(monthly_credits, 500)

primary_contract = {}   # account_id -> dict of its primary contract
for acc in all_account_ids:
    start = YEAR_START  # primary contracts cover the analysis year
    if acc in churned_accounts:
        end = date(2026, random.choice([4, 5, 6, 7]), random.choice([15, 28, 30]))
    else:
        end = YEAR_END
    annual, credits = commit_and_credits(acc in shelf_accounts)
    row = {
        "contract_id": next_contract_id(),
        "account_id": acc,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "annual_commit_dollars": annual,
        "included_monthly_compute_credits": credits,
    }
    contract_rows.append(row)
    primary_contract[acc] = row

# ~150 renewal contracts (sequential, non-overlapping) to reach ~1,200 rows
renewal_pool = [a for a in normal_accounts
                if a not in expansion_accounts and a not in churned_accounts]
for acc in random.sample(renewal_pool, 150):
    prev = primary_contract[acc]
    contract_rows.append({
        "contract_id": next_contract_id(),
        "account_id": acc,
        "start_date": date(2027, 1, 1).isoformat(),
        "end_date": date(2027, 12, 31).isoformat(),
        "annual_commit_dollars": round(prev["annual_commit_dollars"] * random.uniform(1.0, 1.15), 2),
        "included_monthly_compute_credits": prev["included_monthly_compute_credits"],
    })

# Edge Case 4: mid-year expansions — 2nd contract, starts in June,
# HIGHER commit, and dates OVERLAP the primary contract (both active H2 2026)
for acc in expansion_accounts:
    prev = primary_contract[acc]
    contract_rows.append({
        "contract_id": next_contract_id(),
        "account_id": acc,
        "start_date": date(2026, 6, random.randint(1, 28)).isoformat(),
        "end_date": date(2027, 5, 31).isoformat(),  # overlaps primary (ends 2026-12-31)
        "annual_commit_dollars": round(prev["annual_commit_dollars"] * random.uniform(1.3, 2.0), 2),
        "included_monthly_compute_credits": int(prev["included_monthly_compute_credits"] * random.uniform(1.3, 1.8)),
    })

df_contracts = pd.DataFrame(contract_rows)

# ---------------------------------------------------------------------------
# STEP 5: Daily_Usage_Logs (~200,000 rows) with enforced anomalies
# ---------------------------------------------------------------------------
usage_rows = []
log_counter = 0

def add_log(acc: str, d: date, credits: float):
    global log_counter
    log_counter += 1
    usage_rows.append({
        "log_id": f"LOG-{log_counter:07d}",
        "account_id": acc,
        "date": d.isoformat(),
        "compute_credits_consumed": round(max(credits, 0.0), 2),
    })

def spread_over_days(acc: str, days: list, total: float, jitter: float = 0.35):
    """Distribute a monthly total across the chosen days with realistic noise,
    while mathematically preserving the exact total (last day absorbs residual)."""
    if not days or total <= 0:
        return
    weights = np.random.uniform(1 - jitter, 1 + jitter, size=len(days))
    weights = weights / weights.sum()
    amounts = weights * total
    for d, amt in zip(days, amounts):
        add_log(acc, d, float(amt))

monthly_usage_by_account = {a: {m: 0.0 for m in ALL_MONTHS} for a in all_account_ids}

for acc in all_account_ids:
    if acc in shelf_accounts:
        # Edge Case 2: ZERO usage rows. Skip entirely.
        continue

    credits = primary_contract[acc]["included_monthly_compute_credits"]
    annual_credits = credits * 12

    if acc in spike_accounts:
        # Edge Case 1: 90% of ANNUAL credits consumed in Month 1...
        m1_days = month_days(2026, 1)
        m1_total = annual_credits * 0.90
        spread_over_days(acc, m1_days, m1_total)
        monthly_usage_by_account[acc][1] = m1_total
        # ...then 0-2% of annual credits spread thinly over months 2-12
        residual_total = annual_credits * random.uniform(0.0, 0.02)
        residual_per_month = residual_total / 11
        for m in range(2, 13):
            days = sorted(random.sample(month_days(2026, m), k=random.randint(1, 3)))
            spread_over_days(acc, days, residual_per_month)
            monthly_usage_by_account[acc][m] = residual_per_month

    elif acc in overage_accounts:
        # Edge Case 3: EVERY month lands at 120-150% of monthly included credits
        for m in ALL_MONTHS:
            target = credits * random.uniform(1.20, 1.50)
            days = sorted(random.sample(month_days(2026, m), k=random.randint(18, 24)))
            spread_over_days(acc, days, target)
            monthly_usage_by_account[acc][m] = target

    else:
        # Normal accounts: healthy-ish consumption 40-105% of included credits,
        # with a per-account trend; churned accounts stop at contract end
        contract_end = date.fromisoformat(primary_contract[acc]["end_date"])
        base_ratio = random.uniform(0.40, 1.05)
        trend = random.uniform(-0.03, 0.04)  # slight monthly drift
        for m in ALL_MONTHS:
            days_in_m = [d for d in month_days(2026, m) if d <= contract_end]
            if not days_in_m:
                break
            ratio = max(base_ratio + trend * (m - 1), 0.05)
            target = credits * ratio * random.uniform(0.9, 1.1)
            k = min(random.randint(17, 22), len(days_in_m))
            days = sorted(random.sample(days_in_m, k=k))
            spread_over_days(acc, days, target)
            monthly_usage_by_account[acc][m] = target

# Edge Case 5a: exactly 150 orphan logs — account_ids that DO NOT exist
existing_ids = set(all_account_ids)
orphan_ids = set()
while len(orphan_ids) < 40:  # 40 distinct fake ids reused across 150 rows
    fake_id = "ACC-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    if fake_id not in existing_ids:
        orphan_ids.add(fake_id)
orphan_ids = list(orphan_ids)
for _ in range(150):
    d = YEAR_START + timedelta(days=random.randint(0, 364))
    add_log(random.choice(orphan_ids), d, random.uniform(50, 5_000))

# Edge Case 5b: exactly 50 logs from VALID accounts, ~3 months AFTER contract end
for acc in random.sample(sorted(churned_accounts), 25):
    contract_end = date.fromisoformat(primary_contract[acc]["end_date"])
    for _ in range(2):  # 25 accounts x 2 rows = 50 rows
        d = contract_end + timedelta(days=random.randint(90, 100))
        add_log(acc, d, random.uniform(100, 3_000))

df_usage = pd.DataFrame(usage_rows)

# ---------------------------------------------------------------------------
# STEP 6: Account_Health (~50,000 rows) — weekly snapshot per account
#   health_color derived from actual consumption ratio that week/cohort
# ---------------------------------------------------------------------------
health_rows = []
snapshot_dates = []
d = YEAR_START
while d <= YEAR_END:
    snapshot_dates.append(d)      # weekly (every Monday-ish cadence)
    d += timedelta(days=7)        # 53 snapshots -> 1,000 x 53 = 53,000 rows

for acc in all_account_ids:
    credits = primary_contract[acc]["included_monthly_compute_credits"]
    for snap in snapshot_dates:
        m = snap.month
        month_total = monthly_usage_by_account[acc][m]
        weekly_estimate = month_total / 4.33
        ratio = month_total / credits if credits else 0

        if acc in shelf_accounts:
            color = "Red"                      # paying, never adopted
        elif acc in spike_accounts:
            color = "Green" if m == 1 else "Red"
        elif ratio >= 1.15:
            color = "Yellow"                   # heavy overage = billing risk
        elif ratio >= 0.55:
            color = "Green"
        elif ratio >= 0.25:
            color = "Yellow"
        else:
            color = "Red"

        # ~7% random noise so the field isn't perfectly deterministic
        if random.random() < 0.07:
            color = random.choice(["Green", "Yellow", "Red"])

        health_rows.append({
            "health_color": color,
            "account_id": acc,
            "date": snap.isoformat(),
            "compute_credits_consumed": round(max(weekly_estimate * random.uniform(0.8, 1.2), 0.0), 2),
        })

df_health = pd.DataFrame(health_rows)

# ---------------------------------------------------------------------------
# STEP 7: Write CSVs + validation summary
# ---------------------------------------------------------------------------
os.makedirs(OUTPUT_DIR, exist_ok=True)
outputs = {
    "CSM_rep.csv": df_csm,
    "Accounts.csv": df_accounts,
    "Contracts.csv": df_contracts,
    "Account_Health.csv": df_health,
    "Daily_Usage_Logs.csv": df_usage,
}
for fname, df in outputs.items():
    df.to_csv(os.path.join(OUTPUT_DIR, fname), index=False)

# --- Success message with row counts ---
print("=" * 62)
print("  SYNTHETIC B2B SaaS DATASET GENERATED SUCCESSFULLY")
print(f"  Output directory: {OUTPUT_DIR}")
print("=" * 62)
for fname, df in outputs.items():
    print(f"  {fname:<24} {len(df):>10,} rows")
print("-" * 62)

# --- Anomaly verification (proves the edge cases were enforced) ---
print("  EDGE CASE VERIFICATION")
usage_by_acc_month = (
    df_usage.assign(month=pd.to_datetime(df_usage["date"]).dt.month,
                    year=pd.to_datetime(df_usage["date"]).dt.year)
)

# 1. Spike & Drop
sp = usage_by_acc_month[usage_by_acc_month["account_id"].isin(spike_accounts) & (usage_by_acc_month["year"] == 2026)]
m1_share = sp[sp["month"] == 1]["compute_credits_consumed"].sum() / sp["compute_credits_consumed"].sum()
print(f"  1. Spike&Drop: {len(spike_accounts)} accts | Month-1 share of annual usage = {m1_share:.1%}")

# 2. Shelfware
shelf_logs = df_usage[df_usage["account_id"].isin(shelf_accounts)]
avg_shelf_commit = df_contracts[df_contracts["account_id"].isin(shelf_accounts)]["annual_commit_dollars"].mean()
print(f"  2. Shelfware : {len(shelf_accounts)} accts | usage rows = {len(shelf_logs)} | avg commit = ${avg_shelf_commit:,.0f}")

# 3. Overages
ov = usage_by_acc_month[usage_by_acc_month["account_id"].isin(overage_accounts) & (usage_by_acc_month["year"] == 2026)]
ov_monthly = ov.groupby(["account_id", "month"])["compute_credits_consumed"].sum().reset_index()
credit_map = {a: primary_contract[a]["included_monthly_compute_credits"] for a in overage_accounts}
ov_monthly["ratio"] = ov_monthly.apply(lambda r: r["compute_credits_consumed"] / credit_map[r["account_id"]], axis=1)
print(f"  3. Overage   : {len(overage_accounts)} accts | monthly ratio range = {ov_monthly['ratio'].min():.2f}x to {ov_monthly['ratio'].max():.2f}x")

# 4. Expansions
multi = df_contracts.groupby("account_id").size()
exp_check = df_contracts[df_contracts["account_id"].isin(expansion_accounts)]
print(f"  4. Expansion : {len(expansion_accounts)} accts with 2 overlapping contracts (2nd starts June 2026)")

# 5. Orphans / rogue
orphans = df_usage[~df_usage["account_id"].isin(existing_ids)]
print(f"  5. Orphans   : {len(orphans)} logs w/ non-existent account_id | 50 logs ~3 months post contract end")
print("=" * 62)
