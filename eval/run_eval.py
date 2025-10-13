#!/usr/bin/env python3
"""
Evaluation harness for the Agentic RAG system.
Loads per-tenant evaluation questions and checks citation fidelity.
"""

import os
import json
import subprocess
import sys
import argparse
from typing import Dict, List, Any

def load_evaluation_questions(base_dir: str) -> Dict[str, List[Dict]]:
    """Load evaluation questions from U1.json, U2.json, etc."""
    questions = {}
    eval_dir = os.path.join(base_dir, "eval")
    
    for tenant in ["U1", "U2", "U3", "U4"]:
        eval_file = os.path.join(eval_dir, f"{tenant}.json")
        if os.path.exists(eval_file):
            with open(eval_file, "r", encoding="utf-8") as f:
                questions[tenant] = json.load(f)
        else:
            print(f"Warning: No evaluation file found for {tenant}")
            questions[tenant] = []
    
    return questions

def call_cli(tenant: str, query: str, config_path: str, base_dir: str) -> str:
    """Call the CLI with the given parameters"""
    cmd = [
        sys.executable, "-m", "app.main",
        "--tenant", tenant,
        "--query", query,
        "--config", config_path
    ]
    
    env = os.environ.copy()
    env.setdefault("GROQ_DISABLE_TELEMETRY", "1")
    env.setdefault("CHROMADB_ALLOW_TELEMETRY", "false")
    env.setdefault("CHROMA_TELEMETRY_DISABLED", "1")
    env["PYTHONPATH"] = base_dir
    
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            env=env,
            cwd=base_dir
        )
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {e}"

def check_citation_fidelity(output: str, expected_doc_ids: List[str] = None) -> Dict[str, Any]:
    """Check if citations are present and correct"""
    import re
    
    # Look for citation patterns: [n] ... (doc=ID, tenant=Ux, vis=public|private)
    citation_pattern = r'\[(\d+)\].*?\(doc=([^,]+),\s*tenant=([^,]+),\s*vis=([^)]+)\)'
    citations = re.findall(citation_pattern, output)
    
    result = {
        "has_citations": len(citations) > 0,
        "citation_count": len(citations),
        "citations": citations,
        "cited_correctly": False
    }
    
    if expected_doc_ids and citations:
        # Check if any of the cited documents are in the expected list
        cited_doc_ids = [citation[1] for citation in citations]
        result["cited_correctly"] = any(doc_id in expected_doc_ids for doc_id in cited_doc_ids)
    
    return result

def evaluate_question(tenant: str, question: Dict, config_path: str, base_dir: str) -> Dict[str, Any]:
    """Evaluate a single question"""
    query = question.get("q", "")
    expected_allowed = question.get("allowed", True)
    expected_contains = question.get("a_contains", [])
    
    # Call the CLI
    output = call_cli(tenant, query, config_path, base_dir)
    
    # Check if it's a refusal
    is_refusal = output.startswith("Refusal:")
    
    # Check citation fidelity
    citation_info = check_citation_fidelity(output)
    
    # Determine if the result matches expectations
    verdict = {
        "tenant": tenant,
        "query": query,
        "output": output,
        "is_refusal": is_refusal,
        "expected_allowed": expected_allowed,
        "expected_contains": expected_contains,
        "citation_info": citation_info,
        "allowed": not is_refusal if expected_allowed else is_refusal,
        "cited_correctly": citation_info["cited_correctly"] if not is_refusal else True
    }
    
    return verdict

def main():
    parser = argparse.ArgumentParser(description="Run evaluation harness")
    parser.add_argument("--config", default="config.yaml", help="Configuration file path")
    parser.add_argument("--output", default="eval/results.json", help="Output file path")
    args = parser.parse_args()
    
    # Get base directory (parent of eval directory)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, args.config)
    
    # Load evaluation questions
    questions = load_evaluation_questions(base_dir)
    
    results = []
    
    # Evaluate each tenant's questions
    for tenant, tenant_questions in questions.items():
        print(f"Evaluating {len(tenant_questions)} questions for {tenant}...")
        
        for question in tenant_questions:
            verdict = evaluate_question(tenant, question, config_path, base_dir)
            results.append(verdict)
            
            # Print progress
            status = "✓" if verdict["allowed"] and verdict["cited_correctly"] else "✗"
            print(f"  {status} {question.get('q', '')[:50]}...")
    
    # Calculate overall metrics
    total_questions = len(results)
    allowed_questions = sum(1 for r in results if r["allowed"])
    correctly_cited = sum(1 for r in results if r["cited_correctly"])
    
    summary = {
        "total_questions": total_questions,
        "allowed_questions": allowed_questions,
        "correctly_cited": correctly_cited,
        "citation_fidelity": correctly_cited / total_questions if total_questions > 0 else 0,
        "access_control_accuracy": allowed_questions / total_questions if total_questions > 0 else 0
    }
    
    # Save results
    output_data = {
        "summary": summary,
        "results": results
    }
    
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nEvaluation complete!")
    print(f"Total questions: {total_questions}")
    print(f"Allowed questions: {allowed_questions}")
    print(f"Correctly cited: {correctly_cited}")
    print(f"Citation fidelity: {summary['citation_fidelity']:.2%}")
    print(f"Access control accuracy: {summary['access_control_accuracy']:.2%}")
    print(f"Results saved to: {args.output}")

if __name__ == "__main__":
    main()
