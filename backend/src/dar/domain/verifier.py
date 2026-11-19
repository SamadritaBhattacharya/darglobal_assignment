"""Final check of a model answer against the evidence it was given (pure, mostly rule-based).

A sentence is kept only if every number and every capitalised proper name in it appears in the
evidence (or the visitor's question, for names). Unsupported sentences are dropped.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_CITATION = re.compile(r"\[\d+\]")
_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")
_NAME = re.compile(r"\b[A-Z][a-zA-Z]{2,}\b")
_SENTENCES = re.compile(r"(?<=[.!?])\s+|\n+")
_MARKDOWN = re.compile(r"[*_`#>]+|^\s*[-•]\s+", re.MULTILINE)
_CLAUSES = re.compile(r"[:;—–]\s*")
_RANGE = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*(?:to|-|–|—|‑|and|through)\s*(\d[\d,]*(?:\.\d+)?)", re.IGNORECASE)
_ALLOWED_NAMES ={"darglobal", "wasalt", "dar", "global", "sar", "the", "source", "sources"}

NOTE = "I couldn't verify some details in that answer, so I left them out."


@dataclass(frozen=True)
class Verified:
    status: str  # "supported" | "partial" | "unsupported"
    text: str


def _numbers(text: str) -> set[str]:
    return {n.replace(",", "").rstrip(".") for n in _NUMBER.findall(_CITATION.sub("", text))}


def verify(answer: str, evidence: list[str], question: str) -> Verified:
    evidence_text = " ".join(evidence)
    evidence_lower = evidence_text.lower()
    question_lower = question.lower()
    evidence_numbers = _numbers(evidence_text)
    per_item_numbers = [_numbers(item) for item in evidence]

    kept: list[str] = []
    dropped = 0
    for sentence in (s.strip() for s in _SENTENCES.split(answer)):
        if not sentence:
            continue
        if _ranges_stated_together(sentence, per_item_numbers) and _supported(
            sentence, evidence_numbers, evidence_lower, question_lower
        ):
            kept.append(sentence)
        else:
            dropped += 1

    if dropped == 0:
        return Verified("supported", answer)
    if not kept:
        return Verified("unsupported", "")
    return Verified("partial", " ".join(kept) + "\n\n" + NOTE)


def _ranges_stated_together(sentence: str, per_item_numbers: list[set[str]]) -> bool:
    """A range like "84 to 389" is only trusted if both ends sit in the same piece of evidence.

    Catches a real failure: a stray number from elsewhere on the page glued onto the right one.
    Two separate figures that are merely compared ("A is 1,000,000 while B is 4,500,000") are not ranges.
    """
    for low, high in _RANGE.findall(_CITATION.sub("", sentence)):
        pair = {low.replace(",", "").rstrip("."), high.replace(",", "").rstrip(".")}
        if not any(pair <= numbers for numbers in per_item_numbers):
            return False
    return True


def _supported(sentence: str, evidence_numbers: set[str], evidence_lower: str, question_lower: str) -> bool:
    if not _numbers(sentence) <= evidence_numbers:
        return False
    plain = _MARKDOWN.sub("", _CITATION.sub("", sentence))
    for clause in _CLAUSES.split(plain):
        clause = clause.strip()
        for position, word in enumerate(_NAME.findall(clause)):
            lowered = word.lower()
            if lowered in _ALLOWED_NAMES:
                continue
            if position == 0 and clause.startswith(word):
                continue  # a clause-initial capital (sentence start, label, bullet) is not necessarily a name
            if lowered not in evidence_lower and lowered not in question_lower:
                return False
    return True
