# PEIP — Predictive Engineering Intelligence Platform

**Built for SunHacks 2026**

Predictive Engineering Intelligence Platform (PEIP) is an agentic AI system designed to radically improve software reliability and risk mitigation. It performs deep static analysis of GitHub repositories, predicts failure-prone modules before they reach production, assigns health scores, and generates automated dual-view reports tailored for both Developers and C-Suite Executives.

## 🧠 Architecture Overview

PEIP is built on a modular multi-agent pipeline:

- **Data Agent:** Clones the repository and interfaces with the GitHub REST API to extract metadata.
- **Analysis Agent:** Mines git commits via PyDriller (calculating churn/authorship) and extracts cyclomatic complexity & maintainability indexes via Radon.
- **Risk Agent:** Applies a weighted heuristic risk model to identify high-risk modules.
- **Scoring Agent:** Normalizes module health and securely persists intelligence via Supabase.
- **Report Agent:** Synthesizes analysis using LLMs (`gpt-4o-mini`) to generate granular technical action items for developers and high-level ROI/business briefings for the C-Suite.
- **Orchestrator:** Sequences all agents inside an isolated environment and manages state.

The system communicates through persistent state on **Supabase** and is exposed securely via a **FastAPI** backend, primed for consumption by a modern **Next.js** dashboard.

## 🚀 Setup & Installation

### Requirements
- Python 3.10+
- Git
- OpenAI API Key
- GitHub Personal Access Token (PAT)
- Supabase Project (URL & Service Role Key)

### Local Development Environment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/prathmbavge/SunHacks-2k26.git
   cd SunHacks-2k26/peip
   ```

2. **Initialize Python Environment:**
   ```bash
   # Create and activate virtual environment
   python -m venv venv
   # Windows: .\venv\Scripts\Activate.ps1
   # macOS/Linux: source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   Copy the example environment file and insert your keys.
   ```bash
   cp .env.example .env
   ```
   **Required Keys in `.env`:**
   ```
   GITHUB_TOKEN=your_token_here
   OPENAI_API_KEY=your_key_here
   SUPABASE_URL=your_supabase_url
   SUPABASE_SERVICE_KEY=your_supabase_key
   PROJECT_NAME=Predictive Engineering Intelligence Platform
   ```

## ⚡ Usage

To run the platform locally, boot the FastAPI server using Uvicorn:

```bash
uvicorn backend.main:app --reload
```

Then, trigger an analysis sequence via a REST client:

```bash
curl -X POST http://127.0.0.1:8000/api/analyze \
     -H "Content-Type: application/json" \
     -d '{"repo_url":"https://github.com/octocat/Hello-World"}'
```

The pipeline will execute the sequential multi-agent analysis and output the final structural intelligence to Supabase.

---
*Created dynamically for the 24-hour hackathon environment.*
