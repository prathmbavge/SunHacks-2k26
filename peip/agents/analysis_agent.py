import argparse
import subprocess
import json
import os
from pydriller import Repository

def run_analysis_agent(repo_dir: str, out_dir: str, max_commits: int = 200):
    churn_map = {}
    authors_map = {}
    
    print("[AnalysisAgent] Mining commits via PyDriller...")
    count = 0
    for commit in Repository(repo_dir).traverse_commits():
        if count >= max_commits:
            break
        for mod in commit.modified_files:
            path = mod.new_path or mod.old_path
            if not path:
                continue
            churn_map[path] = churn_map.get(path, 0) + 1
            if path not in authors_map:
                authors_map[path] = set()
            authors_map[path].add(commit.author.email)
        count += 1

    print("[AnalysisAgent] Running Radon CC...")
    cc_result = subprocess.run(['radon', 'cc', repo_dir, '-j'], capture_output=True, text=True)
    try:
        cc_data = json.loads(cc_result.stdout) if cc_result.stdout else {}
    except json.JSONDecodeError:
        cc_data = {}

    print("[AnalysisAgent] Running Radon MI...")
    mi_result = subprocess.run(['radon', 'mi', repo_dir, '-j'], capture_output=True, text=True)
    try:
        mi_data = json.loads(mi_result.stdout) if mi_result.stdout else {}
    except json.JSONDecodeError:
        mi_data = {}

    final_data = {}
    all_files = set(list(churn_map.keys()) + list(cc_data.keys()))
    
    for fpath in all_files:
        # Radon output keys are often absolute paths, need rough matching
        cc_val = 0.0
        for k, v in cc_data.items():
            if fpath in k and isinstance(v, list) and len(v) > 0:
                cc_val = float(v[0].get('complexity', 0.0))
                break
                
        mi_val = 100.0
        for k, v in mi_data.items():
            if fpath in k and isinstance(v, dict):
                mi_val = float(v.get('mi', 100.0))
                break

        final_data[fpath] = {
            "churn": churn_map.get(fpath, 0),
            "cyclomatic_complexity": cc_val,
            "maintainability_index": mi_val,
            "unique_authors": len(authors_map.get(fpath, set()))
        }
    
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, 'analysis_output.json'), 'w') as f:
        json.dump(final_data, f, indent=2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--max-commits", type=int, default=200)
    args = parser.parse_args()
    run_analysis_agent(args.repo_dir, args.out_dir, args.max_commits)
