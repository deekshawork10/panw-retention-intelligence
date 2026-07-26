import pandas as pd
import time

def run_agentic_sentinel():
    print("\n" + "="*60)
    print("🤖 INITIALIZING GCS RETENTION AGENT...")
    print("="*60)
    time.sleep(1)

    # 1. Read the golden record scorecard we just generated
    try:
        df = pd.read_excel('Executive_Scorecard_Presentation.xlsx', sheet_name='1_Executive_Scorecard')
    except FileNotFoundError:
        print("❌ Error: Could not find the Scorecard Excel file. Please run generate_excel.py first.")
        return

    # 2. Filter for accounts that require intervention
    anomalies = df[df['activation_status'] == 'Unactivated']
    
    if anomalies.empty:
        print("\n✅ All accounts are healthy or onboarding. No interventions required.")
        return

    print(f"\n⚠️  ALERT: Detected {len(anomalies)} accounts requiring immediate intervention.\n")
    time.sleep(1)

    # 3. Agentic Workflow: Draft remediation plans based on the specific edge case
    for index, row in anomalies.iterrows():
        account = row['account_name']
        arr = row['annual_commit_dollars']
        flag = row['edge_case_flag']
        usage = row['consumption_pct']
        
        print("-" * 60)
        print(f"🔍 ANALYZING ACCOUNT: {account}")
        print(f"💰 ARR AT RISK: {arr}")
        print(f"🚩 ANOMALY DETECTED: {flag} (Usage: {usage})")
        
        time.sleep(1.5)
        print("\n📝 DRAFTING CSM REMEDIATION PLAN...")
        time.sleep(1)
        
        if "Shelfware" in flag:
            print(f">>> ACTION: Auto-creating Salesforce Ticket for CSM.")
            print(f">>> DRAFT EMAIL TO CSM:")
            print(f"    'Subject: URGENT - Zero Usage Detected for {account}'")
            print(f"    'Context: {account} has a contracted ARR of {arr} but has consumed 0 credits over the last 90 days.'")
            print(f"    'Playbook: Please initiate the Executive Deployment Audit workflow immediately. Click here to view the health scorecard.'")
        
        elif "Spike" in flag:
            print(f">>> ACTION: Flagging account for Technical Account Manager (TAM) review.")
            print(f">>> DRAFT EMAIL TO CSM & TAM:")
            print(f"    'Subject: Adoption Stalled - {account}'")
            print(f"    'Context: {account} showed initial usage but has stalled out at {usage} of their 90-day commit.'")
            print(f"    'Playbook: TAM to review migration logs to ensure no technical blockers. CSM to schedule an adoption check-in.'")
        
        print("-" * 60 + "\n")
        time.sleep(1)

    print("✅ AGENT RUN COMPLETE. Awaiting human approval for drafted workflows.")
    print("="*60 + "\n")

if __name__ == "__main__":
    run_agentic_sentinel()