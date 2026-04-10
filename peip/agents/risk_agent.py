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
