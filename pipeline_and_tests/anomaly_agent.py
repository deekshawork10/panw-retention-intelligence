import pandas as pd
import time

def run_agentic_sentinel():
    """
    Executes the deterministic anomaly rules and returns a structured payload
    for the Flask API to serve to the dashboard UI.
    """
    try:
        # Read the scorecard
        df = pd.read_excel('Executive_Scorecard_Presentation.xlsx', sheet_name='1_Executive_Scorecard')
    except FileNotFoundError:
        return {"status": "error", "message": "Could not find the Scorecard Excel file."}

    # Filter for accounts that require intervention
    anomalies = df[df['activation_status'] == 'Unactivated']
    
    if anomalies.empty:
        return {"status": "success", "interventions": []}

    interventions = []

    # Agentic Workflow: Draft remediation plans
    for index, row in anomalies.iterrows():
        account = row['account_name']
        
        # Safely handle currency formatting
        arr_val = row['annual_commit_dollars']
        arr = f"${arr_val:,.2f}" if isinstance(arr_val, (int, float)) else str(arr_val)
        
        flag = str(row.get('edge_case_flag', 'Unknown Anomaly'))
        usage = str(row.get('consumption_pct', '0%'))
        
        action = "Flagged for manual review."
        draft = ""
        
        if "Shelfware" in flag:
            action = "Auto-creating Salesforce Ticket for CSM."
            draft = (
                f"Subject: URGENT - Zero Usage Detected for {account}\n"
                f"Context: {account} has a contracted ARR of {arr} but has consumed 0 credits over the last 90 days.\n"
                f"Playbook: Please initiate the Executive Deployment Audit workflow immediately. Click here to view the health scorecard."
            )
        elif "Spike" in flag:
            action = "Flagging account for Technical Account Manager (TAM) review."
            draft = (
                f"Subject: Adoption Stalled - {account}\n"
                f"Context: {account} showed initial usage but has stalled out at {usage} of their 90-day commit.\n"
                f"Playbook: TAM to review migration logs to ensure no technical blockers. CSM to schedule an adoption check-in."
            )
        else:
            action = "Routing to General CSM Queue."
            draft = f"Subject: Account Health Warning - {account}\nContext: System flagged {account} for {flag}."

        interventions.append({
            "account": account,
            "action": action,
            "draft": draft
        })

    return {
        "status": "success", 
        "interventions": interventions
    }