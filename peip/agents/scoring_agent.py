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
    
    repo_meta_path = os.path.join(os.path.dirname(risk_json), 'repo_meta.json')
    meta_info = {}
    if os.path.exists(repo_meta_path):
        with open(repo_meta_path, 'r') as mf:
            meta_info = json.load(mf)
            
    # Deduplicate logic: check if repo exists
    existing = supabase.table('repositories').select('id').eq('repo_url', repo_url).execute()
    
    if existing.data:
        repo_id = existing.data[0]['id']
        print(f"[ScoringAgent] Existing repo {repo_id} found. Purging old sub-tables and updating...")
        supabase.table('repositories').update({
            'overall_health_score': overall_health,
            'language': meta_info.get('language'),
            'star_count': meta_info.get('star_count'),
            'contributor_count': meta_info.get('contributor_count')
        }).eq('id', repo_id).execute()
        
        # Manually clear to prevent orphaned data ghosts
        supabase.table('module_scores').delete().eq('repo_id', repo_id).execute()
        supabase.table('reports').delete().eq('repo_id', repo_id).execute()
    else:
        repo_res = supabase.table('repositories').insert({
            'repo_url': repo_url,
            'repo_name': repo_name,
            'overall_health_score': overall_health,
            'language': meta_info.get('language'),
            'star_count': meta_info.get('star_count'),
            'contributor_count': meta_info.get('contributor_count')
        }).execute()
        repo_id = repo_res.data[0]['id']
    
    for filepath, metrics in data.items():
        supabase.table('module_scores').insert({
            'repo_id': repo_id,
            'file_path': filepath,
            'health_score': final_scores[filepath],
            'risk_classification': metrics['risk_classification'],
            'churn_count': metrics['raw_metrics']['churn'],
            'complexity_score': metrics['raw_metrics']['cyclomatic_complexity'],
            'radon_mi_score': metrics['raw_metrics']['maintainability_index'],
            'unique_authors': metrics['raw_metrics']['unique_authors']
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
