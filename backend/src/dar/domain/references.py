"""Is this message picking one of the results just shown? ("open the 1st one", "show the image of the second one")"""
from __future__ import annotations

import re
from dataclasses import dataclass

_WORDS = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6, "seventh": 7, "eighth": 8,
          "ninth": 9, "tenth": 10, "1st": 1, "2nd": 2, "3rd": 3, "4th": 4, "5th": 5, "6th": 6, "7th": 7, "8th": 8,
          "9th": 9, "10th": 10}
_THING = r"(?:one|result|listing|option|item|card|property|place|choice)"
_ORDINAL_THING = re.compile(rf"\b(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|\d{{1,2}}(?:st|nd|rd|th))\s+{_THING}\b")
_NUMBERED = re.compile(rf"\b(?:number|no\.?|#)\s*(\d{{1,2}})\b|\b{_THING}\s+(?:number\s+)?(\d{{1,2}})\b|^#?(\d{{1,2}})$")
_LAST = re.compile(rf"\b(?:the\s+)?last\s+{_THING}\b")
# "I want to see the image", "show me the photos", "open it", "more details": a pick with no number at all
_IMPLICIT = re.compile(
    r"^(?:(?:i|we)\s+(?:want|would\s+like|wanna|need)\s+to\s+|can\s+(?:i|you)\s+|please\s+|let'?s\s+)?"
    r"(?:see|show|open|view|get|give)?\s*(?:me\s+)?(?:the\s+|its\s+|their\s+|that\s+)?"
    r"(?:images?|photos?|pictures?|pics?|details|more\s+details|more\s+info(?:rmation)?|link|more|it|that(?:\s+one)?)"
    r"(?:\s+please)?$"
)


@dataclass(frozen=True)
class Pick:
    n: int | None  # which result (1-based); None = the visitor did not say which


def _clean(message: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s#.']", " ", message.lower())).strip(" .")


def pick_reference(message: str, shown: int) -> Pick | None:
    """Returns the picked result number, "which one?" (n=None), or None when this is not a pick at all."""
    text = _clean(message)
    if not text:
        return None
    if _LAST.search(text):
        return Pick(shown) if shown else Pick(1)
    match = _ORDINAL_THING.search(text)
    if match:
        return Pick(_WORDS[match.group(1)])
    numbered = _NUMBERED.search(text)
    if numbered and len(text.split()) <= 7:
        return Pick(int(next(g for g in numbered.groups() if g)))
    if shown and _IMPLICIT.match(text):
        return Pick(1) if shown == 1 else Pick(None)
    return None
