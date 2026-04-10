import argparse
import subprocess
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def parse_github_url(url: str) -> tuple:
    parts = url.rstrip("/").split("/")
    return parts[-2], parts[-1]

def run_data_agent(repo_url: str, out_dir: str):
    owner, repo_name = parse_github_url(repo_url)
    repo_path = os.path.join(out_dir, repo_name)
    
    # Clone the repository
    if not os.path.exists(repo_path):
        print(f"[DataAgent] Cloning repo into {repo_path}")
        result = subprocess.run(['git', 'clone', repo_url, repo_path], capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Git clone failed: {result.stderr}")
    
    # Fetch Metadata from GitHub REST API
    token = os.getenv('GITHUB_TOKEN')
    headers = {"Authorization": f"Bearer {token}"} if token and "your_token_here" not in token else {}
    api_url = f"https://api.github.com/repos/{owner}/{repo_name}"
    
    repo_data = {}
    contributors = []
    
    resp = requests.get(api_url, headers=headers)
    if resp.status_code == 200:
        repo_data = resp.json()
        contrib_resp = requests.get(f"{api_url}/contributors", headers=headers)
        contributors = contrib_resp.json() if contrib_resp.status_code == 200 else []
    else:
        print(f"[DataAgent] Warning: GitHub API returned {resp.status_code}. Mocking metadata.")
    
    meta = {
        "repo_name": repo_name,
        "default_branch": repo_data.get("default_branch", "main"),
        "language": repo_data.get("language", "Unknown"),
        "star_count": repo_data.get("stargazers_count", 0),
        "contributor_count": len(contributors),
        "total_commits_fetched": 0 # updated by next agent
    }
    
    os.makedirs(repo_path, exist_ok=True)
    with open(os.path.join(repo_path, 'repo_meta.json'), 'w') as f:
        json.dump(meta, f, indent=2)
    
    print("[DataAgent] Finished.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-url", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    run_data_agent(args.repo_url, args.out_dir)
