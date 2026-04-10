# Technical Implementation Guide (PEIP)

## Section 1 — Project Setup and Configuration

```bash
# Backend (Python + FastAPI)
mkdir peip && cd peip
python3 -m venv venv && source venv/bin/activate
pip install fastapi uvicorn pydriller radon langchain openai supabase python-dotenv

# Frontend (Next.js)
npx create-next-app@latest frontend --typescript --tailwind --app
cd frontend && npm install @supabase/supabase-js recharts

# Antigravity MCP setup
npx -y @upstash/context7-mcp        # Context7
npx -y @supabase/mcp-server-supabase@latest  # Supabase MCP
```

**.env Configuration:**
```env
GITHUB_TOKEN=ghp_your_token_here
OPENAI_API_KEY=sk-your_key_here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key
REPO_TEMP_DIR=/tmp/peip
```

## Section 2 — Data Agent (`agents/data_agent.py`)

```python
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
    headers = {"Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}"}
    api_url = f"https://api.github.com/repos/{owner}/{repo_name}"
    
    resp = requests.get(api_url, headers=headers)
    if resp.status_code == 404:
        raise RuntimeError("Repository not found (404).")
    elif resp.status_code == 403:
        raise RuntimeError("Rate limit exceeded (403).")
    
    repo_data = resp.json()
    
    # Fetch Contributors
    contrib_resp = requests.get(f"{api_url}/contributors", headers=headers)
    contributors = contrib_resp.json() if contrib_resp.status_code == 200 else []
    
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
```

## Section 3 — Analysis Agent (`agents/analysis_agent.py`)

```python
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
```

## Section 4 — Risk Prediction Agent (`agents/risk_agent.py`)

```python
import argparse
import json
import os

def compute_risk_score(churn: int, max_churn: int, complexity: float, max_complexity: float, mi_score: float, has_tests: bool) -> float:
    """
    Weighted heuristic risk model. All inputs normalized to 0-1 range.
    Higher score = higher risk. Score > 0.7 = High, 0.4-0.7 = Medium, < 0.4 = Low.
    """
    # Churn: files modified most frequently are highest risk (weight 0.40)
    churn_norm = churn / max_churn if max_churn > 0 else 0

    # Complexity: high cyclomatic complexity = harder to maintain (weight 0.35)
    complexity_norm = min(float(complexity) / 20.0, 1.0)  # cap at 20 (very complex)

    # Maintainability Index: Radon scores 0-100, invert so low MI = high risk (weight 0.15)
    mi_norm = 1.0 - (float(mi_score) / 100.0)

    # Test coverage proxy: no test file in repo = higher risk (weight 0.10)
    test_penalty = 0.0 if has_tests else 1.0

    return (churn_norm * 0.40) + (complexity_norm * 0.35) + (mi_norm * 0.15) + (test_penalty * 0.10)

def run_risk_agent(analysis_path: str, out_dir: str):
    with open(analysis_path, 'r') as f:
        data = json.load(f)
        
    if not data:
        return
        
    max_churn = max((v['churn'] for v in data.values()), default=1)
    max_complexity = max((v['cyclomatic_complexity'] for v in data.values()), default=1)
    
    # Check if a test file exists in the repo dict
    has_tests = any('test' in k.lower() for k in data.keys())

    risk_outputs = {}
    for filepath, metrics in data.items():
        score = compute_risk_score(
            metrics['churn'], max_churn,
            metrics['cyclomatic_complexity'], max_complexity,
            metrics['maintainability_index'], has_tests
        )
        
        classification = "Low"
        if score > 0.7:
            classification = "High"
        elif score >= 0.4:
            classification = "Medium"
            
        factors = []
        if metrics['churn'] > max_churn * 0.5: factors.append(f"High churn ({metrics['churn']} modifications)")
        if metrics['cyclomatic_complexity'] > 10: factors.append(f"Cyclomatic complexity {metrics['cyclomatic_complexity']}")
        if not has_tests: factors.append("No test file detected in repo scope")
        
        risk_outputs[filepath] = {
            "risk_score": round(score, 2),
            "risk_classification": classification,
            "contributing_factors": factors,
            "raw_metrics": metrics
        }
        
    with open(os.path.join(out_dir, 'risk_scores.json'), 'w') as f:
        json.dump(risk_outputs, f, indent=2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis-json", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    run_risk_agent(args.analysis_json, args.out_dir)
```

## Section 5 — Scoring Agent (`agents/scoring_agent.py`)

```python
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
    key = os.environ.get("SUPABASE_SERVICE_KEY")
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
        res = supabase.table('module_scores').insert({
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
```

## Section 6 — Report Agent (`agents/report_agent.py`)

```python
import argparse
import json
import os
from openai import OpenAI
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_developer_report(scores_json: str, repo_name: str) -> str:
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
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    supabase: Client = create_client(url, key)
    
    with open(risk_json_path, 'r') as f:
        data = json.load(f)
        
    dev_rep = generate_developer_report(json.dumps(data)[:3000], "Target Repo")
    ceo_rep = generate_ceo_report(json.dumps(data)[:3000], "Target Repo")
    
    supabase.table('reports').insert({'repo_id': repo_id, 'report_type': 'developer', 'content': dev_rep}).execute()
    supabase.table('reports').insert({'repo_id': repo_id, 'report_type': 'ceo', 'content': ceo_rep}).execute()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-id", required=True)
    parser.add_argument("--risk-json", required=True)
    args = parser.parse_args()
    run_report_agent(args.repo_id, args.risk_json)
```

## Section 7 — Orchestrator (`orchestrator.py`)

```python
import subprocess
import os
import json

def run_full_pipeline(repo_url: str):
    repo_name = repo_url.split('/')[-1].replace('.git','')
    base_dir = os.environ.get("REPO_TEMP_DIR", "/tmp/peip")
    repo_dir = os.path.join(base_dir, repo_name)
    
    print("1. Running Data Agent")
    subprocess.run(['python3', 'agents/data_agent.py', '--repo-url', repo_url, '--out-dir', base_dir], check=True)
    
    print("2. Running Analysis Agent")
    subprocess.run(['python3', 'agents/analysis_agent.py', '--repo-dir', repo_dir, '--out-dir', repo_dir], check=True)
    
    print("3. Running Risk Agent")
    analysis_json = os.path.join(repo_dir, "analysis_output.json")
    subprocess.run(['python3', 'agents/risk_agent.py', '--analysis-json', analysis_json, '--out-dir', repo_dir], check=True)
    
    print("4. Running Scoring Agent")
    risk_json = os.path.join(repo_dir, "risk_scores.json")
    subprocess.run(['python3', 'agents/scoring_agent.py', '--risk-json', risk_json, '--repo-url', repo_url], check=True)
    
    # Extract Repo ID implicitly from the output file of Scoring agent
    final_json = os.path.join(repo_dir, "final_scores.json")
    with open(final_json, 'r') as f:
        jdict = json.load(f)
        repo_id = jdict['repo_id']
        overall = jdict['overall']

    print("5. Running Report Agent")
    subprocess.run(['python3', 'agents/report_agent.py', '--repo-id', repo_id, '--risk-json', risk_json], check=True)
    
    return {"repo_id": repo_id, "overall_health_score": overall, "status": "Success"}
```

## Section 8 — FastAPI Backend (`main.py`)

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from supabase import create_client, Client
from orchestrator import run_full_pipeline
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(url, key)

class AnalyzeRequest(BaseModel):
    repo_url: str

@app.post("/api/analyze")
def analyze_repo(req: AnalyzeRequest):
    try:
        res = run_full_pipeline(req.repo_url)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/results/{repo_id}")
def get_results(repo_id: str):
    res = supabase.table('module_scores').select('*').eq('repo_id', repo_id).execute()
    return res.data

@app.get("/api/report/{repo_id}/{type}")
def get_report(repo_id: str, type: str):
    res = supabase.table('reports').select('content').eq('repo_id', repo_id).eq('report_type', type).execute()
    if not res.data:
        raise HTTPException(404, "Report not found")
    return {"content": res.data[0]['content']}

@app.get("/health")
def health():
    return {"status": "ok"}
```

## Section 9 — Next.js Dashboard (`frontend/`)

*(Skeleton examples of components, expand in `/frontend/components/`)*

`app/page.tsx`:
```tsx
import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const [url, setUrl] = useState('');
  const router = useRouter();

  const analyze = async () => {
    const res = await fetch('http://localhost:8000/api/analyze', {
      method: "POST", headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ repo_url: url })
    });
    const data = await res.json();
    router.push(`/dashboard/${data.repo_id}`);
  };

  return (
    <div className="flex flex-col items-center p-10">
      <input type="text" onChange={e=>setUrl(e.target.value)} placeholder="GitHub URL" className="border p-2 text-black"/>
      <button onClick={analyze} className="mt-4 bg-blue-600 text-white p-2">Analyze Repo</button>
    </div>
  );
}
```

`components/OverallScoreGauge.tsx`:
```tsx
import { RadialBarChart, RadialBar, PolarAngleAxis } from 'recharts';

export default function OverallScoreGauge({ score }: { score: number }) {
  const color = score >= 70 ? "#22c55e" : score >= 40 ? "#f59e0b" : "#ef4444";
  const data = [{ name: 'Score', value: score, fill: color }];
  
  return (
    <RadialBarChart width={200} height={200} innerRadius="70%" outerRadius="100%" data={data} startAngle={180} endAngle={0}>
      <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
      <RadialBar background clockWise dataKey="value" />
      <text x={100} y={100} textAnchor="middle" dominantBaseline="middle" className="text-3xl font-bold">{score}</text>
    </RadialBarChart>
  );
}
```

## Section 10 — Deployment via Firebase MCP

Deploy procedure using Firebase MCP logic:
```
1. "Use Firebase MCP to initialize a new Firebase project called peip-dashboard"
2. "Use Firebase MCP to get the web app configuration and write it to frontend/.env.local"
3. "Build the Next.js app: cd frontend && npm run build && npm run export"
4. "Use Firebase MCP to deploy the ./frontend/out directory to Firebase Hosting"
5. "Use Firebase MCP to return the live hosting URL"
```

## Section 11 — 24-Hour Build Timeline

| Hour | Task |
| :--- | :--- |
| **0–1** | MVP / Directory Init via Antigravity |
| **1-3** | Supabase Backend setup & Scaffolding |
| **3-7** | Core local agents (Data, Risk, Analysis, Score) |
| **7-12**| LLM Agent implementations + LangChain orchestrator bindings |
| **13-19**| FastAPI REST implementations & Next.js dashboard |
| **20-22**| Local Validation & Firebase Deploy |

## Section 12 — Testing Strategy

Utilize standard `pytest`. Verify `test_risk_boundary_conditions` locally:
```python
def test_risk_boundary_conditions():
    assert compute_risk_score(0, 10, 0, 10, 100, True) < 0.4 # Low
    assert compute_risk_score(10, 10, 20, 20, 0, False) > 0.7 # High
```
