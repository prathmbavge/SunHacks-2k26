-- Schema for PEIP Project

CREATE TABLE repositories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  repo_url TEXT NOT NULL,
  repo_name TEXT NOT NULL,
  overall_health_score INTEGER,
  language TEXT,
  star_count INTEGER,
  contributor_count INTEGER,
  analyzed_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE module_scores (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  repo_id UUID REFERENCES repositories(id),
  file_path TEXT NOT NULL,
  health_score INTEGER CHECK (health_score BETWEEN 0 AND 100),
  risk_classification TEXT CHECK (risk_classification IN ('Low', 'Medium', 'High')),
  churn_count INTEGER,
  complexity_score FLOAT,
  radon_mi_score FLOAT,
  unique_authors INTEGER
);

CREATE TABLE reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  repo_id UUID REFERENCES repositories(id),
  report_type TEXT CHECK (report_type IN ('developer', 'ceo')),
  content TEXT NOT NULL,
  generated_at TIMESTAMP DEFAULT NOW()
);
