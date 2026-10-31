"""Issue text parsing helpers."""
import re

STOP = {"about", "after", "again", "also", "and", "are", "because", "been", "before", "being", "between", "could", "does", "during", "from", "have", "into", "issue", "just", "more", "most", "other", "please", "should", "some", "than", "that", "their", "them", "then", "there", "these", "they", "this", "through", "under", "until", "using", "very", "want", "when", "where", "which", "while", "with", "would"}


def extract_terms(issue: str, limit: int = 40) -> list[str]:
    """Return useful words and technical tokens in first-seen order."""
    result: list[str] = []
    for token in re.findall(r"[A-Za-z_][A-Za-z0-9_.-]{2,}", issue.lower()):
        for term in token.replace(".", " ").replace("_", " ").replace("-", " ").split():
            if len(term) >= 3 and term not in STOP and term not in result:
                result.append(term)
                if len(result) >= limit:
                    return result
    return result
