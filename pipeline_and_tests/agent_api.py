from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import time

app = Flask(__name__)
CORS(app)

print("⚙️ Initializing Data Engine & Reading Bulk CSVs...")

try:
    df_accounts = pd.read_csv('accounts_data.csv')
    df_contracts = pd.read_csv('contracts_data.csv')
    df_logs = pd.read_csv('daily_usage_logs.csv')
    df_csm = pd.read_csv('csm_rep_data.csv') 
    df_health = pd.read_csv('account_health_data.csv') 
    
    df_contracts['start_date'] = pd.to_datetime(df_contracts['start_date'])
    df_contracts['end_date'] = pd.to_datetime(df_contracts['end_date'])
    df_logs['date'] = pd.to_datetime(df_logs['date'])
    df_health['date'] = pd.to_datetime(df_health['date'])
    print("✅ CSVs Loaded Successfully.")
except Exception as e:
    print(f"❌ Error loading data: {e}")

def get_anchor_date(quarter_str):
    if quarter_str == 'Q1': return pd.to_datetime('2026-03-31')
    elif quarter_str == 'Q2': return pd.to_datetime('2026-06-30')
    elif quarter_str == 'Q3': return pd.to_datetime('2026-09-30')
    else: return pd.to_datetime('2026-12-31') 

def build_master_dataframe(quarter_str, region, segment):
    anchor = get_anchor_date(quarter_str)
    
    # 1. Filter Contracts
    active_contracts = df_contracts[(df_contracts['start_date'] <= anchor) & (df_contracts['end_date'] >= anchor)]
    active_contracts = active_contracts.sort_values('annual_commit_dollars', ascending=False).drop_duplicates('account_id')
    
    # 2. Join Accounts and CSM
    acc_csm = pd.merge(df_accounts, df_csm, left_on='rep_id', right_on='csm_id', how='left')
    if region and region != 'All': acc_csm = acc_csm[acc_csm['region'] == region]
    if segment and segment != 'All': acc_csm = acc_csm[acc_csm['segment'] == segment]
    
    # 3. Calculate Actual System Logs (90-day trailing)
    ninety_days = anchor - pd.Timedelta(days=90)
    recent_logs = df_logs[(df_logs['date'] > ninety_days) & (df_logs['date'] <= anchor)]
    usage_sum = recent_logs.groupby('account_id')['compute_credits_consumed'].sum().reset_index()
    
    # 4. Get the latest Account Health record as of the anchor date
    valid_health = df_health[df_health['date'] <= anchor]
    latest_health = valid_health.sort_values('date', ascending=False).drop_duplicates('account_id')
    latest_health = latest_health[['account_id', 'health_color', 'compute_credits_consumed']].rename(
        columns={'compute_credits_consumed': 'csm_reported_credits'}
    )
    
    # 5. Master Merge
    df_master = pd.merge(acc_csm, active_contracts, on='account_id', how='inner')
    df_master = pd.merge(df_master, usage_sum, on='account_id', how='left').fillna({'compute_credits_consumed': 0})
    df_master = pd.merge(df_master, latest_health, on='account_id', how='left').fillna({
        'health_color': 'Unknown', 
        'csm_reported_credits': 0
    })
    
    # 6. Business Logic Gates
    if len(df_master) > 0:
        df_master['90d_prorated'] = (df_master['included_monthly_compute_credits'] / 30) * 90
        df_master['consumption_pct'] = df_master.apply(
            lambda row: (row['compute_credits_consumed'] / row['90d_prorated']) * 100 if row['90d_prorated'] > 0 else 0, axis=1
        )
        
        def determine_status(row):
            days_active = (anchor - row['start_date']).days
            if days_active < 45: return 'Onboarding'
            if row['consumption_pct'] >= 50: return 'Activated'
            return 'Unactivated'
            
        df_master['activation_status'] = df_master.apply(determine_status, axis=1)
    
    return df_master

def format_currency(val):
    if val >= 1000000: return f"${val/1000000:.2f}M"
    return f"${val/1000:.0f}K"

@app.route('/api/dashboard-metrics', methods=['GET'])
def get_metrics():
    quarter = request.args.get('quarter', 'Q4')
    region = request.args.get('region', 'All')
    segment = request.args.get('segment', 'All')
    
    df = build_master_dataframe(quarter, region, segment)
    if len(df) == 0: return jsonify({"total_arr": "$0", "activated_arr": "$0", "risk_arr": "$0", "anomaly_count": "0 Accounts"})
        
    total_arr = df['annual_commit_dollars'].sum()
    activated_arr = df[df['activation_status'].isin(['Activated', 'Onboarding'])]['annual_commit_dollars'].sum()
    
    return jsonify({
        "total_arr": format_currency(total_arr),
        "activated_arr": format_currency(activated_arr),
        "risk_arr": format_currency(total_arr - activated_arr),
        "anomaly_count": f"{len(df[df['activation_status'] == 'Unactivated'])} Accounts"
    })

@app.route('/api/executive-summary', methods=['GET'])
def get_executive_summary():
    region = request.args.get('region', 'All')
    segment = request.args.get('segment', 'All')
    
    quarters = ["Q1", "Q2", "Q3", "Q4"]
    results = []
    prev_activated = 0
    
    for q in quarters:
        df = build_master_dataframe(q, region, segment)
        total_arr = df['annual_commit_dollars'].sum() if len(df) > 0 else 0
        activated_arr = df[df['activation_status'].isin(['Activated', 'Onboarding'])]['annual_commit_dollars'].sum() if len(df) > 0 else 0
        
        growth = 0
        if prev_activated > 0: growth = ((activated_arr - prev_activated) / prev_activated) * 100
        prev_activated = activated_arr
        
        results.append({
            "quarter": f"{q} 2026",
            "total_arr": format_currency(total_arr),
            "activated_arr": format_currency(activated_arr),
            "risk_arr": format_currency(total_arr - activated_arr),
            "growth": f"+{growth:.1f}%" if growth >= 0 else f"{growth:.1f}%"
        })
    return jsonify(results)

@app.route('/api/table-data', methods=['GET'])
def get_table_data():
    quarter = request.args.get('quarter', 'Q4')
    region = request.args.get('region', 'All')
    segment = request.args.get('segment', 'All')
    
    df = build_master_dataframe(quarter, region, segment)
    demo_names = ["Spike Inc", "Ghost LLC", "Fresh Start", "Grow Corp"]
    demo_df = df[df['company_name'].isin(demo_names)].copy()
    real_anomalies = df[(df['activation_status'] == 'Unactivated') & (~df['company_name'].isin(demo_names))].copy()
    real_anomalies = real_anomalies.sort_values('annual_commit_dollars', ascending=False).head(100)
    
    combined_df = pd.concat([demo_df, real_anomalies])
    table_rows = []
    
    for _, row in combined_df.iterrows():
        name = row['company_name']
        usage = row['consumption_pct']
        health_color = row['health_color']
        
        # Override for the Ghost LLC demo narrative
        if name == "Ghost LLC": 
            health_color = "Green"
            usage = 0 
        
        # DERIVING TICKET SEVERITY FROM CSM HEALTH
        if health_color == "Red":
            ticket_status = "Sev-1 (Blocker)"
        elif health_color == "Yellow":
            ticket_status = "Sev-2/3 (Warning)"
        else:
            ticket_status = "No Critical Tickets"
        
        # AGENT ROUTING LOGIC
        if usage == 0 and health_color == "Green":
            flag = "Critical Data Discrepancy"
            action = "Audit CSM Sync"
            btn_style = "action-btn"
        elif name == "Spike Inc": 
            flag = "Spike & Drop"; action = "Escalate to TAM"; btn_style = "action-btn"
        elif usage == 0: 
            flag = "Shelfware"; action = "Audit Deployment"; btn_style = "action-btn"
        elif name == "Fresh Start": 
            flag = "Grace Period"; action = "Deploying"; btn_style = "action-btn disabled"
        elif name == "Grow Corp": 
            flag = "Mid-Year Expansion"; action = "Healthy"; btn_style = "action-btn disabled"
        elif usage > 0 and usage < 25: 
            flag = "Severe Under-utilization"; action = "Schedule Exec Sync"; btn_style = "action-btn"
        else: 
            flag = "Stalled Adoption"; action = "Draft Outreach Plan"; btn_style = "action-btn"
            
        table_rows.append({
            "account": name,
            "arr_raw": float(row['annual_commit_dollars']),
            "arr": format_currency(row['annual_commit_dollars']),
            "usage": "0%" if usage == 0 else f"{usage:.1f}%",
            "health_color": health_color,
            "tickets": ticket_status, 
            "status": "Unactivated" if (usage == 0 and health_color == "Green" and name == "Ghost LLC") else row['activation_status'],
            "flag": flag,
            "action_text": action,
            "btn_style": btn_style
        })
    return jsonify(table_rows)

@app.route('/api/run-agent', methods=['GET'])
def run_agentic_sentinel():
    results = [
        {"account": "Ghost LLC", "action": "Triggered Data Integrity Audit.", "draft": "Subject: URGENT - False Positive Discrepancy Detected\nContext: CSM marked Account Health as GREEN, but back-end consumption logs show 0% utilization. Routing to RevOps to audit health score validity."},
        {"account": "Spike Inc", "action": "Escalated to Technical Account Manager (TAM).", "draft": "Subject: Adoption Stalled - Spike Inc\nContext: Usage dropped heavily. TAM to review migration logs for technical blockers."}
    ]
    time.sleep(1.5)
    return jsonify({"status": "success", "interventions": results})

if __name__ == "__main__":
    app.run(port=5000, debug=True)