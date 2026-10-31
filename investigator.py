#!/usr/bin/env python3
"""Read-only, evidence-first coding issue investigation CLI."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
from issue_agent.search import investigate
from issue_agent.report import render_report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path, help="Repository directory to inspect")
    parser.add_argument("--issue", required=True, type=Path, help="Text or Markdown bug report")
    parser.add_argument("--out", type=Path, help="Report destination; stdout when omitted")
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--max-files", type=int, default=1500)
    parser.add_argument("--model", action="store_true", help="Use optional configured OpenAI-compatible investigation provider")
    args = parser.parse_args(argv)
    repo = args.repo.expanduser().resolve()
    if not repo.is_dir():
        parser.error(f"repository directory does not exist: {repo}")
    if not 1 <= args.top_k <= 20:
        parser.error("--top-k must be between 1 and 20")
    if not 1 <= args.max_files <= 10000:
        parser.error("--max-files must be between 1 and 10000")
    try:
        issue_path = args.issue.expanduser().resolve(strict=True)
        if not issue_path.is_file():
            raise ValueError("issue path is not a file")
        issue = issue_path.read_text(encoding="utf-8")
        if not issue.strip():
            raise ValueError("issue report is empty")
        if len(issue) > 20_000:
            raise ValueError("issue report exceeds 20,000 characters")
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        parser.error(f"cannot read issue report: {exc}")
    terms, candidates = investigate(repo, issue, args.top_k, args.max_files)
    model_note = ""
    if args.model:
        from issue_agent.provider import configured_provider, ReadOnlyTools
        try:
            evidence = "\n".join(f"{e.path}:{e.line}: {e.text}" for c in candidates for e in c.evidence)
            model_note = configured_provider().investigate(issue, evidence, ReadOnlyTools(repo))
        except (RuntimeError, OSError, ValueError) as exc:
            parser.error(f"model investigation could not run: {exc}")
    report = render_report(repo, issue, terms, candidates, model_note)
    try:
        if args.out:
            out = args.out.expanduser().resolve()
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(report, encoding="utf-8")
            print(f"Wrote investigation report to {out}")
        else:
            print(report)
    except OSError as exc:
        parser.error(f"cannot write report: {exc}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
