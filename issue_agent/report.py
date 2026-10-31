"""Markdown report rendering."""
from pathlib import Path
from .search import Candidate

MAX_REPORT_CHARS = 40_000


def render_report(repo: Path, issue: str, terms: list[str], candidates: list[Candidate], model_note: str = "") -> str:
    title = next((line.strip("# \t") for line in issue.splitlines() if line.strip()), "Coding issue investigation")[:180]
    out = [f"# Investigation: {title}", "", f"**Repository:** `{repo}`", "", "> Read-only investigation. Ranked files are leads; confirm the execution path before treating a cause as established.", "", "## Issue summary", "", issue.strip()[:4000], "", "## Ranked files and evidence", ""]
    if not candidates:
        out.append("No matching eligible source files found. Try a more specific issue report or check the repository path.")
    for i, c in enumerate(candidates, 1):
        out += [f"### {i}. `{c.path}` — score {c.score}", "", f"Signals: {', '.join(f'`{t}`' for t in c.matched_terms) or 'filename match'}", ""]
        out.extend(f"- `{e.path}:{e.line}` — `{e.text}`" for e in c.evidence)
        if not c.evidence:
            out.append("- Filename matched; no matching source line was found.")
        out.append("")
    out += ["## Likely investigation steps", "", "1. Reproduce the reported behavior with the smallest stated input.", "2. Trace the relevant code and callers from the cited snippets; verify that the path reaches the reported behavior.", "3. Compare current behavior with the expected result and inspect nearby tests.", "4. Make the smallest justified change and add a regression test that fails before the fix.", "5. Run the focused test and the repository's relevant broader checks.", "", "## Proposed regression test", "", "Create a focused test using the report's stated input and assert the expected result. Include the unaffected control case described by the reporter. The exact test is provisional until the behavior and API are confirmed.", "", "## Uncertainties", "", "- Retrieval is lexical and may omit semantically relevant files.", "- No root cause is confirmed by ranking alone; validate each hypothesis against execution and tests.", "", "## Questions for the reporter", "", "- What exact input and environment reproduce the issue?", "- What result is expected, and what result currently occurs?", "- Are there compatibility constraints or related tests not mentioned?", ""]
    if model_note:
        out += ["## Model-assisted notes", "", model_note[:8000], ""]
    return "\n".join(out)[:MAX_REPORT_CHARS]
