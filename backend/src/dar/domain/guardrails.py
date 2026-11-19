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
    r"\byou are now\b|\bDAN\b|jailbreak|developer mode|without (any )?restrictions",
    re.IGNORECASE,
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
        "I can't help with changing or revealing how I work. I'm here to answer questions about "
        'DarGlobal projects and Wasalt listings, for example: "Where is Neptune located?"'
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


def check(message: str) -> Refusal | None:
    if len(_NON_LATIN.findall(message)) >= 3:
        return Refusal("language", _REPLIES["language"])
    if _INJECTION.search(message):
        return Refusal("injection", _REPLIES["injection"])
    if _ADVICE.search(message):
        return Refusal("advice", _REPLIES["advice"])
    return None
