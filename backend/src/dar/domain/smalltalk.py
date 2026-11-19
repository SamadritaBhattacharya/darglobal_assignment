"""Greetings and small talk. Answered instantly with no search and no model call.

Only fires when the WHOLE message is small talk. "Hi, tell me about Neptune" is a real question.
"""
from __future__ import annotations

import re

_FILLER = r"(?:\s+(?:there|everyone|all|assistant|bot|team|friend))*"
_GREETING = re.compile(
    rf"^(?:hi+|hello+|hey+|hiya|howdy|greetings|yo|good\s+(?:morning|afternoon|evening|day)|salam|assalamu?\s+alaikum){_FILLER}$"
)
_THANKS = re.compile(rf"^(?:thanks|thank\s+you|thx|ty|cheers|much\s+appreciated|appreciate\s+it)(?:\s+(?:so\s+much|a\s+lot|very\s+much))?{_FILLER}$")
_BYE = re.compile(r"^(?:bye+|goodbye|good\s+bye|see\s+you(?:\s+(?:later|soon))?|take\s+care|cya)$")
_HOW_ARE_YOU = re.compile(r"^(?:how\s+are\s+you(?:\s+doing)?|how\s+is\s+it\s+going|how'?s\s+it\s+going|what'?s\s+up)$")
_ABOUT_ME = re.compile(
    r"^(?:who\s+are\s+you|what\s+are\s+you|what\s+is\s+your\s+name|what\s+can\s+you\s+do|what\s+do\s+you\s+(?:do|know)|"
    r"help(?:\s+me)?|can\s+you\s+help(?:\s+me)?|how\s+can\s+you\s+help(?:\s+me)?|how\s+do\s+(?:i|you)\s+(?:use|work)(?:\s+this)?)$"
)

WHAT_I_DO = (
    "I'm the DarGlobal & Wasalt assistant. I can tell you about DarGlobal's projects (locations, amenities, "
    "partners, investing) and search a sample of Wasalt property listings in Saudi Arabia."
)
TRY_ASKING = (
    "Try asking:\n"
    '- "Where is Neptune located?"\n'
    '- "How does Neptune compare with Marea?"\n'
    '- "Do you have any rentals in Riyadh?"'
)


def _clean(message: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s']", " ", message.lower())).strip()


def reply(message: str) -> str | None:
    text = _clean(message)
    if not text:
        return None
    if _GREETING.match(text):
        return f"Hello! {WHAT_I_DO}\n\n{TRY_ASKING}"
    if _THANKS.match(text):
        return "You're welcome! Ask me anything else about DarGlobal's projects or the Wasalt listings."
    if _BYE.match(text):
        return "Goodbye! Come back any time you'd like to explore DarGlobal's projects or Wasalt listings."
    if _HOW_ARE_YOU.match(text):
        return f"I'm doing well, thank you for asking! {WHAT_I_DO}\n\n{TRY_ASKING}"
    if _ABOUT_ME.match(text):
        return f"{WHAT_I_DO}\n\nI always show where my answers come from, and I'll tell you honestly when something isn't in my data.\n\n{TRY_ASKING}"
    return None
