# Software Requirements Specification (SRS)

## Section 1 — Introduction

The Predictive Engineering Intelligence Platform (PEIP) represents a massive conceptual shift from reactive debugging to proactive failure prediction. As software systems compound in complexity, technical debt and logical entropy silently accumulate in highly modified, unmonitored code regions. PEIP aims to intercept this by integrating directly with GitHub repositories and using a robust, multi-agent AI pipeline to run deep static analysis on the source code. Rather than waiting for a feature to break in production, PEIP evaluates source code maintainability, cyclomatic complexity, and code churn historically, assigning clear, actionable health scores out of 100 on a per-module basis. By extracting this data and surfacing it immediately into two distinct textual views, it enables business executives and software engineers to align their deployment strategies and risk mitigation identically.

**Definitions and Terminology:**

| Term | Definition |
| :--- | :--- |
| **Agent** | A modular, typed Python script within the pipeline assigned to a single analytical workload. |
| **Health Score** | An integer ranging from 0 to 100 denoting the projected stability of a given module, with 100 being completely healthy. |
| **Code Churn** | A metric representing the frequency at which a particular file has been modified across git history. Higher churn implies volatility. |
| **Cyclomatic Complexity** | A quantitative measure of the independent execution paths within a block of code (measured via Radon), directly correlating to difficulty in testing. |
| **Maintainability Index (MI)** | An industry-standard score (0-100) capturing halstead volume, complexity, and lines of code. |
| **Risk Classification** | Categorical mapping of combined metrics into 'Low', 'Medium', or 'High' tiers indicating immediate threat to application security or stability. |
| **PyDriller** | A Python framework utilized by the agents to traverse and mine commit histories directly from the cloned repository. |
| **Radon** | A Python tool utilized for extracting raw cyclomatic complexity and maintainability indices. |
| **Supabase** | The underlying PostgreSQL orchestration database layer responsible for all persistence and cross-agent communication points. |
| **MCP** | Model Context Protocol interactions utilized autonomously by the host agent environment to bridge logical decisions to raw file or API execution. |

## Section 2 — Overall Description

PEIP acts essentially as an autonomous security auditing engine. It consists of a strict multi-agent pipeline composed of five distinct Python agents, coordinated cleanly by a LangChain orchestrator. The state of the entire process is completely isolated within a central Supabase PostgreSQL database, meaning agents do not hold memory, they merely compute inputs (usually raw file system data) and write finalized insights to the tables. A Next.js front-end acts as the interface layer, visualizing these insights directly from the database to avoid workload collisions.

The platform acknowledges three distinct User Classes. First, the **Developer**, who needs explicit file paths, precise error descriptions, and immediate raw scores (e.g., complexity metrics) to target refactoring efforts effectively. Second, the **Engineering Manager**, who focuses on module trends and team-based bottlenecks, observing how churn corresponds to individual contributor efforts. Third, the **CEO/Executive**, who operates completely decoupled from codebase terminology. This user consumes a non-technical impact report addressing business risk, stability translation, and resource allocation.

**Operating Environment:**
The application demands a deployment environment capable of running Python 3.10+ for agent executions alongside Node.js 18+ for the user interface. State management mandates an active Supabase (PostgreSQL) instance. Front-end execution leverages Next.js 14 and Firebase Hosting, while the ML orchestrations depend heavily on LangChain 0.2+, PyDriller 2.x, and Radon 5.x.

## Section 3 — Functional Requirements

| ID | Title | Description | Input | Output | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- |
| FR-001 | GitHub Repository URL Input and Validation | Validates standard GitHub HTTPS URLs to ensure structure before proceeding. | String (GitHub URL) | Boolean (Valid/Invalid) | High |
| FR-002 | Repository Cloning to Local Temp Directory | Automates `git clone` to transfer the target codebase to `/tmp/peip/{repo}`. | Repository URL | Local Repository Files | High |
| FR-003 | Commit History Extraction via PyDriller | Walk graph history to catalog modification distributions across files. | Local Repository Path | JSON Dict of Commits | High |
| FR-004 | Per-File Code Churn Computation | Distill commit history into a simple integer mapping of file path to churn count. | Commit Dict | JSON mapped Integers | High |
| FR-005 | Cyclomatic Complexity Analysis via Radon | Evaluates and assigns an explicit integer score mapping graph paths within functions. | Local Source Files | JSON mapped CC Scores | High |
| FR-006 | Maintainability Index Computation via Radon | Combines raw structure metrics into an index scale for broad comparison. | Local Source Files | JSON mapped MI Scores | High |
| FR-007 | Contributor Activity Tracking | Aggregates commit authors by email domain to observe structural bottlenecking mapping. | Commit Metadata | Int (Unique Authors/File) | Medium |
| FR-008 | Weighted Risk Score Computation | Merges Churn, CC, and MI logically utilizing a strict weighting model to map fractional risk. | Churn, CC, MI JSONs | Float (0.0 to 1.0) | High |
| FR-009 | Risk Classification: Low / Medium / High | Parses fractional risk into a strict ternary category classification tier system. | Risk Float | String Tier | High |
| FR-010 | Health Score Assignment 0–100 per Module | Inverts risk data into an easily digestible percentage mapped out of 100. | Risk Float | Integer [0-100] | High |
| FR-011 | Repository-Level Overall Health Score | Combines module-based score averages biased heavily by modification frequency sizes. | Module Scores List | Integer [0-100] | High |
| FR-012 | Supabase Schema Creation and Data Persistence | Creates Postgres constraints ensuring schema conformity and writes data directly to cloud. | SQL Statements, DB Keys | DB Rows Created | High |
| FR-013 | Developer Report Generation via LLM | Structures raw integer and file inputs into an actionable paragraph formatting. | Module Scores JSON | String (Markdown Rep) | High |
| FR-014 | CEO Report Generation via LLM (non-technical) | Abstracts code specifics into a business-ready conceptual evaluation text summary. | Module Scores JSON | String (Markdown Rep) | High |
| FR-015 | Dual View Mode Toggle on Dashboard | Next.js state interaction to visually swap between technical table mappings and text summary. | Button Activity Event | UI Rerender | Medium |
| FR-016 | Risk Heatmap and Commit Trend Visualization | Processes JSON metrics out of Supabase into `Recharts` graph structures instantly. | Supabase Metrics Table | `Recharts` UI Output | Medium |

## Section 4 — Non-Functional Requirements

**Performance:** The complete pipeline must execute in under 90 seconds for any repository holding fewer than 500 total commits. Because PyDriller traverses commit diffs structurally inside a loop, it inherently acts as the immediate execution bottleneck. To alleviate thread stalling for the Minimal Viable Product demonstration, an explicit cap constraint of 200 maximum commits has been applied directly to the traversal scripts.

**Security:** No raw environment credentials (such as GitHub Authentication Tokens or OpenAI API Keys) will be stored in accessible databases or shared with the language models. They will reside entirely inside `.env` configurations that are injected strictly at runtime via `python-dotenv`. Supabase integrations must utilize Row-Level Security (RLS) constraints universally to prevent data corruption endpoints.

**Reliability:** Strict fault tolerance is demanded by the multi-agent design paradigm. Each single agent is wrapped intrinsically in individual `try/except` configurations. If an agent faults on bad Python formatting or API limits, it will explicitly write a failed execution error state directly to Supabase rather than blowing up the pipeline thread completely, allowing the Orchestrator to identify exactly where the break occurred and to theoretically retry safely.

**Usability:** The CEO prompt response has a rigid requirement for absolutely zero engineering technical terms out of the resultant string. It is validated strictly against a "5th-grader text constraint test". Any usage of terms like "cyclomatic complexity" or "git tree" implies a prompt failure requiring immediate LLM revision tweaking.

**Maintainability:** Each agent is specifically coded structurally to run isolated. For instance, testing the Data Agent mandates zero interaction with the Formatting Agent whatsoever. An engineer simply executes `python3 agents/scoring_agent.py --help` explicitly, as all functions take defined CLI arguments mapped to temporary system directories mapping intermediate input and outputs. 

## Section 5 — External Interface Requirements

1. **GitHub API**: The app invokes REST v3 specifically for contributor demographics and repository scale. Must factor standard API rate limiting configurations (5,000 authenticated requests an hour). Pagination handled safely sequentially via `Link:` header parses over requests.
2. **PyDriller**: Directly utilizes the internal `Repository` class via standard python package executions. Intercepts code modifications distinctly focusing on the `traverse_commits()` iterator referencing the `modified_files` attribute cleanly.
3. **Radon CLI**: Acts completely externally on Python execution shells using standard commands like `radon cc -j` mapped to file locations rather than invoking pure python integrations to prevent Python specific thread blocking overheads.
4. **Supabase**: Data transfer heavily relies on standard generic `supabase-py` HTTP integrations and basic SQL syntax application via client matching schemas.
5. **LLM API (OpenAI)**: `gpt-4o-mini` accessed standardly using native openai dependencies setting max completion token windows rigidly to 1500 for massive Dev logs, and restricting Business tier logs to 800 token caps.
6. **Next.js Framework**: Uses completely strict asynchronous REST polling endpoints via standard web browser integration pointing right to FastAPI mappings.

## Section 6 — Constraints and Assumptions

- Due strictly to GitHub's REST rate limits, massive historical repository data structures cannot be completely scoured cleanly in singular 1-second interactions. The ceiling analysis cap explicitly assumes a subset (approximately latest 200 - 500 items max depending heavily on pagination speeds) is satisfactory for structural risk indexing without blocking app operations indefinitely.
- Radon assumes python execution. Standard `.py` file structures are guaranteed to properly generate complexities and CC indexes. If executed forcefully against `.js` or `.ts` heavy builds, Radon logic simply falls backwards intelligently, using heavily skewed "code-churn only" mathematics naturally due to output lackings.
- The standard user Supabase cloud integration structure holds completely to standard Free-Tier caps implicitly. Limits like 500MB max raw storage or 2GB max monthly bandwidth distributions are safely assumed as more than sufficient for general standard execution overheads during hackathon constraints.
