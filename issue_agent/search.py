"""Bounded, read-only repository search and evidence collection."""
from dataclasses import dataclass
from pathlib import Path
import re
from .parsing import extract_terms

SKIP_DIRS = {".git", ".hg", ".svn", ".venv", "venv", "node_modules", "vendor", "dist", "build", "__pycache__", ".next", "coverage", "target", "out", "bower_components"}
SOURCE_SUFFIXES = {".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rs", ".rb", ".php", ".cs", ".cpp", ".c", ".h", ".hpp", ".md", ".json", ".yaml", ".yml", ".toml", ".html", ".css", ".sh"}
MAX_FILE_BYTES = 500_000
MAX_EVIDENCE_PER_FILE = 5
MAX_EVIDENCE_TOTAL = 30

@dataclass
class Evidence:
    path: str
    line: int
    text: str
    matched_terms: list[str]

@dataclass
class Candidate:
    path: str
    score: int
    matched_terms: list[str]
    evidence: list[Evidence]


def _eligible(repo: Path, path: Path) -> bool:
    try:
        parts = path.relative_to(repo).parts
        resolved = path.resolve()
        if not resolved.is_relative_to(repo.resolve()):
            return False
        return not any(p.startswith(".") or p in SKIP_DIRS for p in parts) and path.suffix.lower() in SOURCE_SUFFIXES and path.stat().st_size <= MAX_FILE_BYTES
    except (OSError, ValueError):
        return False


def source_files(repo: Path, max_files: int = 1500):
    """Yield eligible files deterministically; never follows directory symlinks."""
    count = 0
    try:
        for base, dirs, files in __import__("os").walk(repo, followlinks=False):
            dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d not in SKIP_DIRS)
            for name in sorted(files):
                path = Path(base) / name
                if _eligible(repo, path):
                    yield path
                    count += 1
                    if count >= max_files:
                        return
    except OSError:
        return


def investigate(repo: Path, issue: str, top_k: int = 8, max_files: int = 1500):
    terms = extract_terms(issue)
    # Exact error/message matches are a strong signal; identifiers and filename hits are explained separately.
    phrases = [s.strip().strip("`\"'") for s in re.findall(r"(?:`[^`]+`|\"[^\"]{4,}\"|'[^']{4,}')", issue) if len(s.strip()) >= 4]
    candidates: list[Candidate] = []
    evidence_count = 0
    for path in source_files(repo, max_files):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(repo).as_posix()
        path_low = rel.lower()
        path_hits = [t for t in terms if t in path_low]
        matched: set[str] = set(path_hits)
        evidence: list[Evidence] = []
        pending_evidence: list[tuple[int, Evidence]] = []
        exact_hits = sum(1 for phrase in phrases if phrase.lower() in "\n".join(lines).lower())
        for number, line in enumerate(lines, start=1):
            low = line.lower()
            hits = [term for term in terms if re.search(r"(?<![a-z0-9_])" + re.escape(term) + r"(?![a-z0-9_])", low)]
            matched.update(hits)
            if hits:
                pending_evidence.append((len(hits), Evidence(rel, number, line.strip()[:240], hits)))
        pending_evidence.sort(key=lambda item: (-item[0], item[1].line))
        evidence = [item for _, item in pending_evidence[:MAX_EVIDENCE_PER_FILE]] if evidence_count < MAX_EVIDENCE_TOTAL else []
        evidence_count += len(evidence)
        overlap = len(matched)
        score = overlap + 3 * len(path_hits) + 8 * exact_hits
        if score:
            candidates.append(Candidate(rel, score, sorted(matched), evidence))
    candidates.sort(key=lambda c: (-c.score, c.path))
    return terms, candidates[:max(1, min(top_k, 20))]
