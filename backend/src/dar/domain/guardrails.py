"""Input guardrails: decide, before any retrieval or model call, whether to refuse a message.

Conservative, readable rules. They reduce risk; they do not replace the verifier or the evals.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Refusal:
    kind: str
    reply: str


_INJECTION = re.compile(
    r"ignore (all |any )?(the |your )?(previous|prior|above|earlier)|"
    r"disregard (your|the|all|any)|"
    r"(reveal|show|print|repeat|output|tell me|give me) (me )?(your|the) (hidden |secret )?(system )?(prompt|instructions|rules)|"
    r"(text|instructions|everything) above|hidden instructions|"
    r"\byou are now\b|\bDAN\b|jailbreak|developer mode|without (any )?restrictions|"
    r"pretend (?:to be|you are|you're|that you)|"
    r"\bfrom now on\b.{0,40}\b(?:you|answer|respond|ignore)\b|"
    r"act as (?:my|a|an|the)\s+(?:developer|admin|administrator|root|unrestricted|unfiltered|jailbroken|dan)\b|"
    r"forget (?:everything|all|your|what)\b.{0,30}\b(?:told|instructions|rules|said|above|before)\b|"
    r"</?system>|^\s*system\s*:|\[system\]|###\s*(?:instruction|system)|"
    r"bypass (?:your|the|all)?\s*(?:filters?|rules|guardrails|restrictions|safety)|"
    r"(?:repeat|print|output|say|recite|reproduce)\s+(?:the\s+)?(?:words|text|everything|all)\s+(?:above|before)|"
    r"(?:original|initial|first|hidden|secret|real)\s+(?:instructions|prompt|rules)|"
    r"translate\s+(?:your|the)\s+(?:instructions|prompt|rules|system)|"
    r"(?:i am|i'm)\s+your\s+(?:developer|creator|admin|owner|programmer)|\bdebug mode\b|\badmin mode\b|\bgod mode\b|\bsudo\b|"
    r"override\s+(?:your|the)\s+(?:rules|instructions|safety)",
    re.IGNORECASE | re.MULTILINE,
)
_ADVICE = re.compile(
    r"\bshould i (invest|buy|put|sell|purchase)|"
    r"good (investment|idea to (buy|invest))|"
    r"will (the )?(prices?|property|market|values?) (go up|rise|increase|fall|drop)|"
    r"(legal|tax|financial|investment|mortgage) advice|"
    r"guarantee[sd]?\b.{0,40}\b(returns?|profits?|roi|yield|gains?)\b|"
    r"promise (me )?.{0,40}\b(not lose|no loss|profit|returns?|make money)\b|"
    r"(not|never|won't|will not) lose (any )?money",
    re.IGNORECASE,
)
_NON_LATIN = re.compile(r"[Ѐ-ӿ֐-ۿݐ-ݿऀ-ॿ぀-ヿ一-鿿가-힯]")

_REPLIES = {
    "injection": (
        "I can't share details about how I work, and I can't change my rules. "
        "I can help with DarGlobal projects and a sample of Wasalt listings, "
        'for example: "Where is Neptune located?"'
    ),
    "advice": (
        "I can't give investment, legal, tax or financial advice, and I can't predict prices. "
        "I can share facts from DarGlobal's and Wasalt's published information, such as locations, "
        "amenities and listing details. For advice, please speak to a licensed professional, "
        "or visit darglobal.co.uk."
    ),
    "language": (
        "Sorry, I can only answer in English for now. Please ask your question in English and "
        "I'll look it up in the DarGlobal and Wasalt information."
    ),
}


def looks_like_injection(text: str) -> bool:
    """True if text reads like an instruction aimed at an AI (used on retrieved page text, which is data only)."""
    return bool(_INJECTION.search(text))


def check(message: str) -> Refusal | None:
    if len(_NON_LATIN.findall(message)) >= 3:
        return Refusal("language", _REPLIES["language"])
    if _INJECTION.search(message):
        return Refusal("injection", _REPLIES["injection"])
    if _ADVICE.search(message):
        return Refusal("advice", _REPLIES["advice"])
    return None
