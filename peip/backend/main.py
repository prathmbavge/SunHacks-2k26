import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Add peip root to path so agents can be imported correctly regardless of cwd
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from agents.orchestrator import run_full_pipeline

# Load configuration from .env file
load_dotenv()

app = FastAPI(
    title=os.getenv("PROJECT_NAME", "Predictive Engineering Intelligence Platform"),
    description="PEIP Backend API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

url = os.environ.get("SUPABASE_URL", "")
key = os.environ.get("SUPABASE_KEY", "")

supabase = None
if url and key and "your_supabase" not in url:
    from supabase import create_client, Client
    try:
        supabase = create_client(url, key)
    except Exception as e:
        print(f"Warning: Failed to initialize Supabase client: {e}")

class AnalyzeRequest(BaseModel):
    repo_url: str

@app.post("/api/analyze")
def analyze_repo(req: AnalyzeRequest):
    try:
        res = run_full_pipeline(req.repo_url)
        if res.get("status") == "Error":
            return res
            
        repo_id = res.get("repo_id")
        overall = res.get("overall_health_score")
        
        if not supabase:
            # Return mocked payload if Env vars missing
            return {
                "status": "Success",
                "repo": {"overall_health_score": overall, "language": "Mocked", "star_count": 0, "contributor_count": 0},
                "modules": [{"file_path": "src/demo.py", "risk_classification": "High", "health_score": 40, "churn_count": 15, "complexity_score": 12}],
                "reports": [{"report_type": "developer", "content": "## Mocked\n- Need Supabase keys"}, {"report_type": "ceo", "content": "## Mocked\n- Missing DB config"}]
            }
            
        # Hydrate via the flattened schema
        repo_data = supabase.table('repositories').select('*').eq('id', repo_id).execute()
        repo_obj = repo_data.data[0] if repo_data.data else {"overall_health_score": overall}
        
        modules_data = supabase.table('module_scores').select('*').eq('repo_id', repo_id).execute()
        reports_data = supabase.table('reports').select('*').eq('repo_id', repo_id).execute()
        
        return {
            "status": "Success",
            "repo": repo_obj,
            "modules": modules_data.data,
            "reports": reports_data.data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/results/{repo_id}")
def get_results(repo_id: str):
    if not supabase:
        return [{"mocked": True, "repo_id": repo_id, "health_score": 85}]
    
    res = supabase.table('module_scores').select('*').eq('repo_id', repo_id).execute()
    return res.data

@app.get("/api/report/{repo_id}/{report_type}")
def get_report(repo_id: str, report_type: str):
    if not supabase:
        return {"content": f"Mock {report_type} report content for {repo_id} due to missing keys."}
        
    res = supabase.table('reports').select('content').eq('repo_id', repo_id).eq('report_type', report_type).execute()
    if not res.data:
        raise HTTPException(404, "Report not found")
    return {"content": res.data[0]['content']}

@app.get("/health")
def health_check():
    """Health check route to ensure the server is running."""
    return {"status": "ok", "supabase_connected": supabase is not None}
