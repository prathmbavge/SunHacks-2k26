import subprocess
import os
import json

def run_full_pipeline(repo_url: str):
    repo_name = repo_url.split('/')[-1].replace('.git','')
    base_dir = os.environ.get("REPO_TEMP_DIR", "/tmp/peip")
    repo_dir = os.path.join(base_dir, repo_name)
    
    print("1. Running Data Agent")
    subprocess.run(['python', 'agents/data_agent.py', '--repo-url', repo_url, '--out-dir', base_dir], check=True)
    
    print("2. Running Analysis Agent")
    subprocess.run(['python', 'agents/analysis_agent.py', '--repo-dir', repo_dir, '--out-dir', repo_dir], check=True)
    
    print("3. Running Risk Agent")
    analysis_json = os.path.join(repo_dir, "analysis_output.json")
    subprocess.run(['python', 'agents/risk_agent.py', '--analysis-json', analysis_json, '--out-dir', repo_dir], check=True)
    
    print("4. Running Scoring Agent")
    risk_json = os.path.join(repo_dir, "risk_scores.json")
    subprocess.run(['python', 'agents/scoring_agent.py', '--risk-json', risk_json, '--repo-url', repo_url], check=True)
    
    # Extract Repo ID implicitly from the output file of Scoring agent
    final_json = os.path.join(repo_dir, "final_scores.json")
    if not os.path.exists(final_json):
        print("Scoring Agent failed to mock or connect to Supabase, bypassing orchestration completion.")
        return {"status": "Error", "message": "Failed to extract database keys."}
        
    with open(final_json, 'r') as f:
        jdict = json.load(f)
        repo_id = jdict.get('repo_id', 'mocked_id')
        overall = jdict.get('overall', 0)

    print("5. Running Report Agent")
    subprocess.run(['python', 'agents/report_agent.py', '--repo-id', str(repo_id), '--risk-json', risk_json], check=True)
    
    return {"repo_id": repo_id, "overall_health_score": overall, "status": "Success"}
