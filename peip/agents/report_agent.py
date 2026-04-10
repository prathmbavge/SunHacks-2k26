import argparse
import json
import os
from openai import OpenAI
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key and "your_key" not in api_key else None

def generate_developer_report(scores_json: str, repo_name: str) -> str:
    if not client:
        return f"Mock Developer Report for {repo_name} (No API Key)"
    prompt = f"""You are a senior software engineer reviewing {repo_name}.
Based on the following module health analysis, write a technical report for the engineering team.

Data: {scores_json}

Your report must include:
1. Executive summary (2 sentences — overall health score and top concern)
2. High-risk modules (list each with: file path, risk score, specific reasons)
3. Medium-risk modules (list with brief explanation)
4. Recommended actions (specific, actionable: "Refactor auth.py — cyclomatic complexity of 14 exceeds the 10-unit threshold")
5. Testing gaps (files with no test counterpart in /tests/)

Temperature: 0.3. Be specific. Use file names. Do not generalize."""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3, max_tokens=1500
    )
    return resp.choices[0].message.content

def generate_ceo_report(scores_json: str, repo_name: str) -> str:
    if not client:
        return f"Mock CEO Report for {repo_name} (No API Key)"
    prompt = f"""You are a business analyst briefing a CEO on software risk.
The engineering team analyzed {repo_name} and found the following:

Data: {scores_json}

Write a 3-paragraph executive briefing. Rules:
- Zero technical terms. No "cyclomatic complexity", no "churn", no "modules".
- Replace technical concepts with business concepts: 
    "high churn file" → "part of the product that changes constantly and is prone to breaking"
    "low health score" → "area of the product at high risk of causing outages"
- Paragraph 1: Current state (what works well, what is at risk)
- Paragraph 2: Business impact (what happens if the risky areas break — customer impact, downtime cost estimate)
- Paragraph 3: Recommended investment (where to focus engineering effort and why it protects revenue)

Temperature: 0.6. Be direct. Every sentence must mean something to a non-engineer."""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6, max_tokens=800
    )
    return resp.choices[0].message.content

def run_report_agent(repo_id: str, risk_json_path: str):
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key or "your_supabase" in url:
        print("[ReportAgent] Skipping database write because keys are placeholders.")
        return
        
    supabase: Client = create_client(url, key)
    
    with open(risk_json_path, 'r') as f:
        data = json.load(f)
        
    dev_rep = generate_developer_report(json.dumps(data)[:3000], "Target Repo")
    ceo_rep = generate_ceo_report(json.dumps(data)[:3000], "Target Repo")
    
    supabase.table('reports').insert({'repo_id': repo_id, 'report_type': 'developer', 'content': dev_rep}).execute()
    supabase.table('reports').insert({'repo_id': repo_id, 'report_type': 'ceo', 'content': ceo_rep}).execute()
    print("[ReportAgent] Finished saving LLM generated reports.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-id", required=True)
    parser.add_argument("--risk-json", required=True)
    args = parser.parse_args()
    run_report_agent(args.repo_id, args.risk_json)
