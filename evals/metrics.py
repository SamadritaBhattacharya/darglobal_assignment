"""Retrieval metrics (pure functions). A "source" is a page URL; repeated chunks of one page count once."""
from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable, Sequence


def _unique(urls: Sequence[str]) -> list[str]:
    return list(dict.fromkeys(urls))


def recall_at_k(retrieved: Sequence[str], expected: Sequence[str], k: int) -> float:
    """Share of the expected sources that appear in the top-k distinct retrieved sources."""
    top = set(_unique(retrieved)[:k])
    return sum(e in top for e in expected) / len(expected) if expected else 1.0


def reciprocal_rank(retrieved: Sequence[str], expected: Sequence[str]) -> float:
    """1 / rank of the first expected source (rank counted over distinct sources); 0 if none found."""
    for rank, url in enumerate(_unique(retrieved), start=1):
        if url in expected:
            return 1.0 / rank
    return 0.0


def context_precision(retrieved: Sequence[str], expected: Sequence[str], k: int) -> float:
    """Share of the top-k distinct retrieved sources that were actually wanted."""
    top = _unique(retrieved)[:k]
    return sum(u in expected for u in top) / len(top) if top else 0.0


def context_recall(expected_facts: Sequence[str], retrieved_texts: Iterable[str]) -> float:
    """Share of the expected facts that appear (case-insensitively) in the retrieved text."""
    if not expected_facts:
        return 1.0
    haystack = " ".join(retrieved_texts).lower()
    return sum(f.lower() in haystack for f in expected_facts) / len(expected_facts)


def mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


# ---- answer metrics ---------------------------------------------------------------------------------

_CITATION = re.compile(r"\[\d+\]")
_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")
_DASHES = dict.fromkeys(map(ord, "‐‑‒–—−"), "-")


def _plain(text: str) -> str:
    """Lower-case with typographic variants (non-breaking hyphens/spaces, dashes) folded to plain ones."""
    return unicodedata.normalize("NFKC", text).translate(_DASHES).lower()


def fact_recall(expected_facts: Sequence[str], answer: str) -> float:
    """Share of the expected facts stated (case-insensitively, ignoring typographic variants) in the answer."""
    if not expected_facts:
        return 1.0
    plain = _plain(answer)
    return sum(_plain(f) in plain for f in expected_facts) / len(expected_facts)


def _numbers(text: str) -> set[str]:
    return {n.replace(",", "").rstrip(".") for n in _NUMBER.findall(_CITATION.sub("", _plain(text)))}


def numbers_grounded(answer: str, source_texts: Iterable[str]) -> bool:
    """True if every number in the answer appears in the cited sources (a rule-based faithfulness check)."""
    return _numbers(answer) <= _numbers(" ".join(source_texts))


def abstention_stats(rows: Sequence[tuple[bool, bool]]) -> dict[str, float]:
    """rows = (should_abstain, abstained). Precision: of the abstentions, how many were right.
    Recall: of the questions that needed one, how many got one."""
    abstained = [r for r in rows if r[1]]
    needed = [r for r in rows if r[0]]
    correct = sum(1 for should, did in rows if should and did)
    return {
        "precision": correct / len(abstained) if abstained else 1.0,
        "recall": correct / len(needed) if needed else 1.0,
    }


def hallucination_rate(rows: Sequence[tuple[bool, bool]]) -> float:
    """rows = (should_abstain, answered). Share of should-abstain questions that were answered anyway."""
    unanswerable = [r for r in rows if r[0]]
    return sum(1 for _, answered in unanswerable if answered) / len(unanswerable) if unanswerable else 0.0
