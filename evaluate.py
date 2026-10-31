"""Evaluate retrieval overlap on explicitly labeled benchmark cases."""
import argparse
import json
from pathlib import Path
from issue_agent.search import investigate

REQUIRED = {"id", "synthetic", "source_revision", "repo", "issue", "relevant_files"}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", type=Path, default=Path("benchmark.json"))
    args = parser.parse_args()
    try:
        cases = json.loads(args.benchmark.read_text(encoding="utf-8"))
        if not isinstance(cases, list) or not cases:
            raise ValueError("benchmark must be a non-empty JSON array")
        totals = {"precision": 0.0, "recall": 0.0}
        for index, case in enumerate(cases, 1):
            missing = REQUIRED - case.keys()
            if missing: raise ValueError(f"case {index} missing fields: {', '.join(sorted(missing))}")
            if not case["source_revision"] or not isinstance(case["synthetic"], bool): raise ValueError(f"case {index} needs a source_revision and boolean synthetic label")
            repo, issue_path = Path(case["repo"]), Path(case["issue"])
            if not repo.is_dir() or not issue_path.is_file(): raise ValueError(f"case {case['id']}: repo or issue file not found")
            relevant = case["relevant_files"]
            if not isinstance(relevant, list) or not relevant: raise ValueError(f"case {case['id']}: relevant_files must be a non-empty array")
            _, candidates = investigate(repo.resolve(), issue_path.read_text(encoding="utf-8"))
            predicted = {candidate.path for candidate in candidates}
            overlap = predicted & set(relevant)
            precision = len(overlap) / len(predicted) if predicted else 0.0
            recall = len(overlap) / len(relevant)
            totals["precision"] += precision; totals["recall"] += recall
            label = "synthetic" if case["synthetic"] else "labeled"
            print(f"{case['id']} [{label}, {case['source_revision']}]: precision={precision:.2f} recall={recall:.2f} matched={sorted(overlap)}")
        n = len(cases)
        print(f"macro averages across {n} case(s): precision={totals['precision']/n:.2f} recall={totals['recall']/n:.2f}")
        print("File overlap does not measure diagnosis accuracy, evidence quality, or test usefulness.")
        return 0
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError, TypeError) as exc:
        parser.error(f"invalid benchmark: {exc}")

if __name__ == "__main__": raise SystemExit(main())
