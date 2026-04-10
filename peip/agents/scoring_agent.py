import argparse
import json
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def run_scoring_agent(risk_json: str, repo_url: str):
    with open(risk_json, 'r') as f:
        data = json.load(f)
        
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")  # Using correct key from .env.example
    
    if not url or not key or "your_supabase" in url:
        print("[ScoringAgent] Mocking Supabase persistence because keys are placeholders.")
        # Proceed mock logic later, failing for now if we want true integration
        return
        
    supabase: Client = create_client(url, key)
    
    repo_name = repo_url.split('/')[-1].replace('.git','')
    
    # Calculate overall health
    total_weight = 0
    total_score = 0
    final_scores = {}
    
    for filepath, metrics in data.items():
        health_score = round((1.0 - metrics['risk_score']) * 100)
        weight = metrics['raw_metrics']['churn'] if metrics['raw_metrics']['churn'] > 0 else 1
        total_score += (health_score * weight)
        total_weight += weight
        final_scores[filepath] = health_score
        
    overall_health = int(total_score / total_weight) if total_weight > 0 else 100
    
    # Store in Supabase
    repo_res = supabase.table('repositories').insert({
        'repo_url': repo_url,
        'repo_name': repo_name,
        'overall_health_score': overall_health
    }).execute()
    
    repo_id = repo_res.data[0]['id']
    
    for filepath, metrics in data.items():
        # First create the module
        mod_res = supabase.table('modules').insert({
            'repo_id': repo_id,
            'file_path': filepath,
            'churn_count': metrics['raw_metrics']['churn'],
            'complexity_score': metrics['raw_metrics']['cyclomatic_complexity'],
            'radon_mi_score': metrics['raw_metrics']['maintainability_index'],
            'unique_authors': metrics['raw_metrics']['unique_authors']
        }).execute()
        mod_id = mod_res.data[0]['id']
        
        # Then the risk score link
        supabase.table('risk_scores').insert({
            'module_id': mod_id,
            'risk_classification': metrics['risk_classification'],
            'health_score': final_scores[filepath]
        }).execute()
        
    with open(os.path.join(os.path.dirname(risk_json), 'final_scores.json'), 'w') as f:
        json.dump({"repo_id": repo_id, "overall": overall_health, "modules": final_scores}, f)
        
    print(f"[ScoringAgent] Saved repo {repo_id} with score {overall_health}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--risk-json", required=True)
    parser.add_argument("--repo-url", required=True)
    args = parser.parse_args()
    run_scoring_agent(args.risk_json, args.repo_url)
