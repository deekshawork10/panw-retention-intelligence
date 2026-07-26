import pandas as pd

# 1. FINAL SCORECARD (The view for the panel with inline edge-case explanations)
scorecard_data = {
    "account_name": ["Healthy Corp", "Spike Inc", "Ghost LLC", "Grow Corp", "Fresh Start", "Unknown (ORPHAN-999)"],
    "annual_commit_dollars": ["$120,000", "$120,000", "$300,000", "$240,000", "$500,000", "N/A"],
    "90d_prorated_commit": ["3,000", "3,000", "7,500", "6,000", "N/A", "N/A"],
    "90d_consumption": [2800, 1100, 0, 5500, 150, 800],
    "consumption_pct": ["93%", "36%", "0%", "91%", "N/A", "N/A"],
    "activation_status": ["Activated", "Unactivated", "Unactivated", "Activated", "Onboarding", "Quarantined"],
    "activated_arr": ["$120,000", "$0", "$0", "$240,000", "$500,000", "$0"],
    "edge_case_flag": [
        "Baseline / Healthy", 
        "Spike & Drop", 
        "Shelfware", 
        "Mid-Year Expansion", 
        "New Customer Grace Period", 
        "Orphaned Usage"
    ],
    "business_logic_explanation": [
        "Passes the 50% gate with 93% sustained usage. The full $120k is recognized as healthy Activated ARR.",
        "Failed the 50% gate (only 36% usage). The rolling 90-day window successfully dampened an initial migration spike, flagging the account as unactivated ($0 aARR) to prevent late-stage churn surprises.",
        "Zero usage logs against a $300k contract. Pipeline automatically zeros out Activated ARR and flags for immediate CSM intervention.",
        "Overlapping contracts ($120k upgraded to $240k mid-year). SQL window functions seamlessly collapsed the timeline to prevent double-counting. Prorated baseline correctly updated to the new 2,000 credits/mo tier.",
        "Customer signed <45 days ago. To prevent artificially tanking Q4 executive metrics, the pipeline bypasses the 50% gate and grants 'Onboarding' status. Full $500k is safely recognized.",
        "System detected 800 credits consumed without a matching CRM account ID. Assertions quarantined the data to prevent falsely inflating another account's metrics."
    ]
}

# 2. DATA DICTIONARY (Explains the column names and math to the panel)
definitions_data = {
    "Column Name": [
        "annual_commit_dollars", 
        "90d_prorated_commit", 
        "90d_consumption", 
        "consumption_pct", 
        "activation_status", 
        "activated_arr",
        "edge_case_flag"
    ],
    "Business Definition & Logic": [
        "Total booked Annual Recurring Revenue (ARR) per the CRM (Contracts table).",
        "The dynamic denominator. Formula: (Included Monthly Credits / 30) * 90. Dynamically blends overlapping contracts using SQL gaps-and-islands logic.",
        "The dynamic numerator. Total compute credits consumed over the trailing 90 days (Usage table).",
        "Formula: 90d_consumption / 90d_prorated_commit.",
        "The gate output. Activated (>= 50%), Unactivated (< 50%), Onboarding (< 45 days old), or Quarantined (Bad Data).",
        "The final North Star metric. Equals annual_commit_dollars if Activated/Onboarding. Equals $0 if Unactivated or Quarantined.",
        "Operational flag triggered by specific SQL logic to categorize anomalies."
    ]
}

# 3. RAW CONTRACTS (The Financial Truth)
contracts_data = {
    "account_id": ["ACC-001", "ACC-002", "ACC-003", "ACC-004", "ACC-004", "ACC-005"],
    "account_name": ["Healthy Corp", "Spike Inc", "Ghost LLC", "Grow Corp", "Grow Corp", "Fresh Start"],
    "contract_id": ["CON-101", "CON-102", "CON-103", "CON-104A", "CON-104B", "CON-105"],
    "annual_commit_dollars": ["$120,000", "$120,000", "$300,000", "$120,000", "$240,000", "$500,000"],
    "monthly_credits": [1000, 1000, 2500, 1000, 2000, 4000],
    "start_date": ["2026-01-01", "2026-01-01", "2026-06-01", "2026-01-01", "2026-09-01", "2026-12-15"],
    "end_date": ["2026-12-31", "2026-12-31", "2027-05-31", "2026-08-31", "2027-08-31", "2027-12-14"]
}

# 4. RAW USAGE (The Product Truth)
usage_data = {
    "account_id": ["ACC-001", "ACC-002", "ACC-003", "ACC-004", "ACC-005", "ORPHAN-999"],
    "total_90d_credits_consumed": [2800, 1100, 0, 5500, 150, 800]
}

# Create DataFrames
df_scorecard = pd.DataFrame(scorecard_data)
df_definitions = pd.DataFrame(definitions_data)
df_contracts = pd.DataFrame(contracts_data)
df_usage = pd.DataFrame(usage_data)

# Write to a multi-tab Excel file with styling
excel_filename = "Executive_Scorecard_Presentation.xlsx"
with pd.ExcelWriter(excel_filename, engine='xlsxwriter') as writer:
    # Write sheets
    df_scorecard.to_excel(writer, sheet_name='1_Executive_Scorecard', index=False)
    df_definitions.to_excel(writer, sheet_name='2_Metric_Definitions', index=False)
    df_contracts.to_excel(writer, sheet_name='3_Raw_Contracts', index=False)
    df_usage.to_excel(writer, sheet_name='4_Raw_Usage', index=False)
    
    # Access workbook and sheets for formatting
    workbook = writer.book
    sheet_scorecard = writer.sheets['1_Executive_Scorecard']
    sheet_definitions = writer.sheets['2_Metric_Definitions']
    
    # Create a format for wrapping text (great for descriptions)
    wrap_format = workbook.add_format({'text_wrap': True, 'valign': 'top'})
    header_format = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1})
    
    # Format Scorecard Sheet
    sheet_scorecard.set_column('A:A', 20) # Account Name
    sheet_scorecard.set_column('B:G', 18) # Metrics
    sheet_scorecard.set_column('H:H', 25) # Edge Case Flag
    sheet_scorecard.set_column('I:I', 60, wrap_format) # Business Logic Explanation (Wide & Wrapped)
    
    # Format Definitions Sheet
    sheet_definitions.set_column('A:A', 25, wrap_format)
    sheet_definitions.set_column('B:B', 80, wrap_format)

print(f"Success! '{excel_filename}' has been generated. Open this in Excel to review.")