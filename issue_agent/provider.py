"""Optional model provider interface. Baseline mode has no provider dependency."""
from abc import ABC, abstractmethod

class InvestigationProvider(ABC):
    @abstractmethod
    def investigate(self, issue: str, evidence: str, tools: "ReadOnlyTools") -> str:
        """Return a cautious diagnosis grounded in supplied evidence."""

class ReadOnlyTools:
    """Bounded repository tools, constrained to a selected root."""
    def __init__(self, repo, max_calls=8, max_output=12000):
        self.repo = repo.resolve()
        self.calls = 0
        self.max_calls = max_calls
        self.max_output = max_output

    def _path(self, relative):
        from pathlib import Path
        if not isinstance(relative, str) or not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise ValueError("path must be a repository-relative path")
        target = (self.repo / relative).resolve()
        if not target.is_relative_to(self.repo):
            raise ValueError("path escapes selected repository")
        return target

    def _charge(self):
        self.calls += 1
        if self.calls > self.max_calls:
            raise ValueError("tool-call limit exceeded")

    def list_files(self, prefix=""):
        from .search import source_files
        self._charge()
        base = self._path(prefix) if prefix else self.repo
        if not base.is_dir():
            raise ValueError("directory does not exist")
        lines = [p.relative_to(self.repo).as_posix() for p in source_files(self.repo) if p.is_relative_to(base)]
        return "\n".join(lines)[:self.max_output]

    def search(self, query):
        from .search import source_files
        self._charge()
        if not isinstance(query, str) or not query.strip() or len(query) > 200:
            raise ValueError("query must contain 1-200 characters")
        found = []
        for p in source_files(self.repo):
            try:
                for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                    if query.lower() in line.lower():
                        found.append(f"{p.relative_to(self.repo).as_posix()}:{n}: {line.strip()[:240]}")
                        if len(found) >= 40: return "\n".join(found)[:self.max_output]
            except (OSError, UnicodeDecodeError):
                continue
        return "\n".join(found)[:self.max_output]

    def read_range(self, relative, start, end):
        self._charge()
        if not isinstance(start, int) or not isinstance(end, int) or start < 1 or end < start or end - start > 100:
            raise ValueError("line range must be 1-101 lines")
        p = self._path(relative)
        from .search import _eligible
        if not p.is_file() or not _eligible(self.repo, p):
            raise ValueError("file is not an eligible repository source file")
        lines = p.read_text(encoding="utf-8").splitlines()
        return "\n".join(f"{i}: {lines[i-1]}" for i in range(start, min(end, len(lines)) + 1))[:self.max_output]


def configured_provider():
    """No bundled network client: explicitly explain provider configuration is not implemented yet."""
    raise RuntimeError("Model investigation is not configured in this prototype. The provider interface is ready, but no API adapter is bundled; use baseline retrieval or implement an adapter for your approved provider.")

class OpenAICompatibleProvider(InvestigationProvider):
    """Small stdlib Chat Completions adapter; requires explicit user configuration."""
    def __init__(self, api_key, model, endpoint="https://api.openai.com/v1/chat/completions"):
        self.api_key, self.model, self.endpoint = api_key, model, endpoint

    def investigate(self, issue, evidence, tools):
        import json, urllib.request
        funcs = [
            {"type":"function","function":{"name":"search","description":"Search eligible repository source lines","parameters":{"type":"object","properties":{"query":{"type":"string"}},"required":["query"],"additionalProperties":False}}},
            {"type":"function","function":{"name":"list_files","description":"List eligible repository files, optionally under a relative directory","parameters":{"type":"object","properties":{"prefix":{"type":"string"}},"additionalProperties":False}}},
            {"type":"function","function":{"name":"read_range","description":"Read 1-101 lines from an eligible repository file","parameters":{"type":"object","properties":{"relative":{"type":"string"},"start":{"type":"integer"},"end":{"type":"integer"}},"required":["relative","start","end"],"additionalProperties":False}}},
        ]
        messages = [{"role":"system","content":"Investigate cautiously. Only report a suspected cause when evidence supports it. Cite every substantive repository claim using path:line from gathered evidence. Use tools only when helpful. End with concise diagnosis, next step, and uncertainty."}, {"role":"user","content":f"Issue:\n{issue[:4000]}\n\nInitial evidence:\n{evidence[:12000]}"}]
        for _ in range(9):
            payload = json.dumps({"model":self.model,"messages":messages,"tools":funcs,"tool_choice":"auto","temperature":0}).encode()
            req = urllib.request.Request(self.endpoint, payload, {"Authorization":f"Bearer {self.api_key}","Content-Type":"application/json"})
            with urllib.request.urlopen(req, timeout=45) as response:
                data = json.loads(response.read(1_000_000))
            msg = data["choices"][0]["message"]
            calls = msg.get("tool_calls") or []
            if not calls:
                answer = msg.get("content") or ""
                # Require cited locations to occur in gathered output (initial or tool results).
                import re
                refs = re.findall(r"(?:[\w.-]+/)*[\w.-]+:\d+", answer)
                gathered = "\n".join(m.get("content", "") for m in messages if m.get("role") in ("user", "tool"))
                if not refs or any(ref not in gathered for ref in refs):
                    raise ValueError("model final answer must cite paths and line numbers present in gathered evidence")
                return answer[:8000]
            messages.append(msg)
            for call in calls[:8]:
                name = call["function"]["name"]
                args = json.loads(call["function"].get("arguments") or "{}")
                if name == "search": result = tools.search(args.get("query"))
                elif name == "list_files": result = tools.list_files(args.get("prefix", ""))
                elif name == "read_range": result = tools.read_range(args.get("relative"), args.get("start"), args.get("end"))
                else: raise ValueError("model requested an unsupported tool")
                messages.append({"role":"tool","tool_call_id":call["id"],"content":result[:12000]})
        raise ValueError("model tool-call limit exceeded before a cited final answer")


def configured_provider():
    import os
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("set OPENAI_API_KEY to enable --model")
    model = os.environ.get("CODING_ISSUE_MODEL", "gpt-4o-mini")
    endpoint = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1/chat/completions").rstrip("/")
    if not endpoint.endswith("/chat/completions"):
        endpoint += "/chat/completions"
    return OpenAICompatibleProvider(key, model, endpoint)
