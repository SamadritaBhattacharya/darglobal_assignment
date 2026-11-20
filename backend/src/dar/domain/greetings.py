"""A greeting at the start of a sentence ("hi", "good morning", "hello there,"): split it from what follows."""
from __future__ import annotations

import re

_PREFIX = re.compile(
    r"^\s*(?:hi+|hello+|hey+|hiya|howdy|greetings|yo|salam|assalamu?\s+alaikum|good\s+(?:morning|afternoon|evening|day))\b"
    r"(?:\s+(?:there|everyone|all|assistant|bot|team|friend))*\s*[,!.\-]*\s*",
    re.IGNORECASE,
)


_TIMED = re.compile(r"^\s*(?:good\s+)?(morning|afternoon|evening|day)\b", re.IGNORECASE)


def greeting_phrase(sentence: str) -> str:
    """Which greeting was used, so the reply can match it: "good morning", or otherwise plain "hello"."""
    timed = _TIMED.match(sentence)
    return f"good {timed.group(1).lower()}" if timed else "hello"


def strip_greeting(sentence: str) -> tuple[bool, str]:
    """(greeted, rest): "hi i am sam" -> (True, "i am sam"); "history of Neptune" -> (False, unchanged)."""
    match = _PREFIX.match(sentence)
    if not match:
        return False, sentence
    return True, sentence[match.end():].strip()
