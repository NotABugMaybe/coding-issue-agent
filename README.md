# Coding Issue Investigator

A Python prototype that turns a bug report into a bounded, read-only investigation report. It ranks likely files, cites line-numbered evidence, and suggests ways for a developer to investigate and validate the issue. It does not modify the selected repository or execute its code.

## Requirements and setup

- Python 3.10 or newer
- No third-party dependencies for baseline retrieval

Clone or copy this folder, then run commands from its root:

```sh
python3 --version
python3 investigator.py --repo sample_repo --issue examples/issue.md --out reports/sample-investigation.md
```

To inspect another repository, pass its local directory and a UTF-8 text or Markdown issue file:

```sh
python3 investigator.py --repo /path/to/checkout --issue /path/to/bug.md --top-k 8 --max-files 1500
```

Omit `--out` to print Markdown to stdout. The issue must be non-empty and no larger than 20,000 characters. `--top-k` is limited to 1–20; `--max-files` to 1–10,000. Output is capped at 40,000 characters.

## Optional model investigation

Baseline mode always works without credentials. The optional `--model` mode uses an OpenAI-compatible Chat Completions endpoint through Python's standard library. Set `OPENAI_API_KEY`; optionally set `CODING_ISSUE_MODEL` (default `gpt-4o-mini`) and `OPENAI_BASE_URL` (default OpenAI endpoint), then run:

```sh
OPENAI_API_KEY=... python3 investigator.py --repo sample_repo --issue examples/issue.md --model
```

The model receives the issue and bounded initial evidence plus read-only `search`, `list_files`, and `read_range` tools. Tool paths are constrained to eligible files under the selected repository; arguments, call count, line ranges, and output are capped. A final answer without citations to gathered `path:line` evidence is rejected. Model service calls send the issue text and retrieved repository snippets to the configured endpoint; use only with data your organization permits sending there. If model setup or a request fails, the CLI reports that failure rather than claiming a model ran.

## Architecture

- `issue_agent/parsing.py`: extracts bounded search terms from issue text.
- `issue_agent/search.py`: filters and scans eligible source files, ranks candidates, and collects line-numbered evidence.
- `issue_agent/provider.py`: optional provider interface and bounded repository tools.
- `issue_agent/report.py`: creates the Markdown report.
- `investigator.py`: validates CLI inputs and connects the stages.
- `evaluate.py`: scores retrieved-file overlap against labeled cases.

Ranking combines distinct term overlap, filename matches, and exact quoted phrase matches. Scores are explainable signals, not probabilities or proof of root cause. Search is deterministic and lexical.

## Safety boundaries and limits

Repository inspection is read-only: the baseline only walks and reads eligible files. It does not launch processes, import project modules, or make changes to the selected repository. Hidden paths, common dependency/build/generated directories, unsupported extensions, files over 500 KB, and files that cannot be decoded as UTF-8 are skipped. Scans default to 1,500 files; evidence is limited to five snippets per file and 30 total; report text is capped. The model tools enforce repository containment and bounded calls/ranges. The report states uncertainty and does not promote a retrieval lead to a confirmed cause.

These controls reduce exposure but do not make this a security boundary against a compromised runtime or endpoint. Model mode sends selected text to the configured provider. Review its data handling and endpoint configuration before use.

## Example report

`reports/sample-investigation.md` is generated from `examples/issue.md` against the included sample repository. It demonstrates the output format; it is not an independent diagnosis or performance claim.

## Evaluation

`benchmark.json` is an explicit JSON array. Each case contains:

- `id`: unique human-readable case name.
- `synthetic`: boolean identifying synthetic fixture cases.
- `source_revision`: immutable commit identifier or explicit fixture revision label.
- `repo`: local repository directory, relative to the command's working directory or absolute.
- `issue`: UTF-8 issue file path, relative to the working directory or absolute.
- `relevant_files`: known relevant repository-relative paths.

The included `sample-discounted-cart-total` case is synthetic and uses the fixed fixture label `synthetic-v1`; it is not an upstream project benchmark. Do not add real cases unless the source revision and expected files are known. Run:

```sh
python3 evaluate.py --benchmark benchmark.json
```

The evaluator reports per-case and macro precision/recall for retrieved paths. These numbers measure file overlap only. Use a separate human review for diagnosis accuracy, evidence quality, and test usefulness. Suggested 0–2 scale per dimension: 0 = incorrect/unsupported or unusable; 1 = partly correct with gaps; 2 = correct and useful with citations. Record reviewer, rationale, and disagreement; do not combine this rubric into retrieval metrics.

## What is implemented and what remains

Implemented: read-only lexical retrieval, bounded evidence and report generation, CLI validation, optional provider interface/adapter, constrained model tools, explicit synthetic benchmark metadata, retrieval overlap evaluation, and unit tests.

Not established: semantic retrieval quality, diagnosis accuracy, production readiness, deployment, reliability on arbitrary repositories, or any real-world performance metric. Model mode depends on a compatible remote service and has not been tested against a live endpoint here. Treat this as a prototype for evaluation and supervised investigation, not a production incident-response system.

## Interview guidance

Describe it as a **prototype** while it is locally runnable and lightly evaluated. Call it a **benchmark** only when cases have pinned revisions and reviewed expected files. Call it a **pilot** only after supervised use with documented outcomes. Claim **production** use only after deployment, operational controls, monitoring, privacy review, and observed reliability exist. This repository does not establish a pilot or production deployment.
