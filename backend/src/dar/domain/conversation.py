"""Everyday conversation: greetings, who the assistant is, remembering the visitor's name, and politely
declining questions about how the assistant is built.

Only fires when EVERY sentence of the message is conversation. "Hi, tell me about Neptune" is a real question.
Answers are written from templates: no search and no model call, so they are free and can never leak anything.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from dar.domain.names import extract_name

_FILLER = r"(?:\s+(?:there|everyone|all|assistant|bot|team|friend))*"
_GREETING = re.compile(
    rf"^(?:hi+|hello+|hey+|hiya|howdy|greetings|yo|good\s+(?:morning|afternoon|evening|day)|salam|assalamu?\s+alaikum){_FILLER}$"
)
_THANKS = re.compile(rf"^(?:thanks|thank\s+you|thx|ty|cheers|much\s+appreciated|appreciate\s+it)(?:\s+(?:so\s+much|a\s+lot|very\s+much))?{_FILLER}$")
_BYE = re.compile(r"^(?:bye+|goodbye|good\s+bye|see\s+you(?:\s+(?:later|soon))?|take\s+care|cya)$")
_HOW_ARE_YOU = re.compile(r"^(?:how\s+are\s+you(?:\s+doing)?|how\s+is\s+it\s+going|how'?s\s+it\s+going|what'?s\s+up)$")
_HELP = re.compile(
    r"^(?:what\s+can\s+you\s+do|what\s+do\s+you\s+(?:do|know)|help(?:\s+me)?|can\s+you\s+help(?:\s+me)?|"
    r"how\s+can\s+you\s+help(?:\s+me)?|how\s+(?:do|can)\s+i\s+use(?:\s+this)?)$"
)
_IDENTITY = re.compile(
    r"^(?:who\s+are\s+you|what\s+are\s+you|what(?:\s+is|'?s)\s+your\s+name|your\s+name|may\s+i\s+know\s+your\s+name|"
    r"are\s+you\s+(?:a\s+|an\s+)?(?:bot|robot|human|person|real|real\s+person|ai|chatbot|machine|assistant|real\s+human)|"
    r"who\s+(?:made|built|created|developed|designed|programmed|trained)\s+you|who\s+is\s+your\s+(?:creator|developer|maker|owner))$"
)
_NAME_QUESTION = re.compile(
    r"^(?:(?:do|can|could)\s+you\s+(?:still\s+)?(?:remember|know|recall)\s+(?:my\s+name|who\s+i\s+am)|"
    r"what(?:\s+is|'?s)\s+my\s+name|who\s+am\s+i|say\s+my\s+name|tell\s+me\s+my\s+name|my\s+name)$"
)
# Questions about how the assistant is built. Each pattern needs the assistant itself as the subject, so
# "what technology does Alpha Residences use?" (a project question) is NOT matched.
_INTERNALS = [re.compile(p) for p in (
    r"\byour\s+(?:\w+\s+){0,2}(?:architectures?|tools?|tech(?:nology|nologies)?|tech\s*stack|stack|frameworks?|models?|llms?|"
    r"prompts?|instructions?|rules|guidelines|configuration|config|settings|functions?|apis?|database|backend|source|training)\b",
    r"\b(?:architectures?|tools?|technolog\w+|tech\s*stack|stack|frameworks?|models?|llms?|apis?|databases?|functions?)\b"
    r"[^.?!]{0,30}\byou\s+(?:can\s+)?(?:have|use|run|call|rely|are\s+(?:built|made|using|based|running|powered))",
    r"\bare\s+you\s+(?:built|made|based|powered|running|using)\b|\bare\s+you\s+(?:a\s+|an\s+)?(?:chat\s*gpt|gpt-?\d*|claude|gemini|llama|bard|copilot|llm|language\s+model)\b",
    r"\bgpt-?\d\b|\bor\s+claude\b",
    r"\bwhat\s+(?:model|llm|ai|technology|tech|framework|stack|database|language)\s+(?:are\s+you|do\s+you\s+use|is\s+behind\s+you|powers\s+you|were\s+you)\b",
    r"\bwhich\s+(?:model|llm|ai)\b.*\byou\b",
    r"\bwhat\s+(?:are|were)\s+you\s+(?:built|made|trained|programmed)\s+(?:with|on|using)\b|\bwhat\s+technolog\w+\s+(?:were|are)\s+you\b",
    r"\bhow\s+do\s+you\s+(?:work|function|operate)\b|\bhow\s+(?:are|were)\s+you\s+(?:built|made|created|trained|programmed|implemented)\b",
    r"\bhow\s+does\s+(?:this|the)\s+(?:chatbot|bot|assistant|app)\s+work\b",
)]

CAN_HELP = (
    "I can help with DarGlobal's projects (locations, amenities, partners, investing) and a sample of "
    "Wasalt property listings in Saudi Arabia."
)
IDENTITY = (
    "I'm the DarGlobal & Wasalt assistant, an AI assistant for exploring DarGlobal's projects and Wasalt listings. "
    "I'm an AI, not a person, so you can simply call me the assistant."
)
INTERNALS_REFUSAL = "I can't share details about how I'm built, the tools behind me, or my instructions."
TRY_ASKING = (
    "Try asking:\n"
    '- "Where is Neptune located?"\n'
    '- "How does Neptune compare with Marea?"\n'
    '- "Do you have any rentals in Riyadh?"'
)
NO_NAME_YET = (
    "I don't know your name yet. Tell me by saying “my name is …” and I'll remember it for this chat "
    "(it stays in your browser)."
)


@dataclass(frozen=True)
class Conversation:
    text: str
    verdict: str  # "answered" | "refused"


def _clean(sentence: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s'\-]", " ", sentence.lower())).strip()


def _kind(sentence: str) -> str | None:
    text = _clean(sentence)
    if not text:
        return None
    if any(p.search(text) for p in _INTERNALS):
        return "internals"
    for kind, pattern in (("greeting", _GREETING), ("thanks", _THANKS), ("bye", _BYE), ("how_are_you", _HOW_ARE_YOU),
                          ("help", _HELP), ("identity", _IDENTITY), ("name_question", _NAME_QUESTION)):
        if pattern.match(text):
            return kind
    if extract_name(sentence):
        return "name_statement"
    return None


def respond(message: str, name: str | None) -> Conversation | None:
    """A conversational reply, or None if any part of the message is a real question for the knowledge base."""
    sentences = [s for s in re.split(r"[.!?\n]+", message) if s.strip()]
    kinds = [_kind(s) for s in sentences]
    if not kinds:
        return None
    if "internals" in kinds:
        # A probe for how the assistant is built is declined wherever it appears, even with friendly chatter around it.
        other_questions = any(k is None for k in kinds)
        text = f"{INTERNALS_REFUSAL} {CAN_HELP}"
        if other_questions:
            text += " If you had another question, please ask it on its own and I'll look it up."
        return Conversation(text=f"{text}\n\n{TRY_ASKING}", verdict="refused")
    if any(k is None for k in kinds):
        return None

    learned = extract_name(message)
    who = learned or name
    parts: list[str] = []
    seen: set[str] = set()
    for kind in kinds:
        if kind in seen:
            continue
        seen.add(kind)
        if kind == "greeting":
            parts.append(f"Hello, {who}!" if who else "Hello!")
        elif kind == "thanks":
            parts.append("You're welcome!")
        elif kind == "bye":
            parts.append("Goodbye! Come back any time.")
        elif kind == "how_are_you":
            parts.append("I'm doing well, thank you for asking!")
        elif kind == "name_statement":
            parts.append(f"Nice to meet you, {learned}!")
        elif kind == "name_question":
            parts.append(f"Yes, your name is {who}." if who else NO_NAME_YET)
        elif kind == "identity":
            parts.append(IDENTITY)
        elif kind == "help":
            parts.append(f"{CAN_HELP} I always show where my answers come from, and I'll say so honestly when something isn't in my data.")
        elif kind == "internals":
            parts.append(f"{INTERNALS_REFUSAL} {CAN_HELP}")

    wants_examples = bool(seen & {"greeting", "how_are_you", "help", "identity", "internals"})
    if wants_examples and "help" not in seen and "internals" not in seen and "identity" not in seen:
        parts.append(CAN_HELP)
    text = " ".join(parts[:1]) + (("\n\n" + "\n\n".join(parts[1:])) if len(parts) > 1 else "")
    if wants_examples:
        text += f"\n\n{TRY_ASKING}"
    return Conversation(text=text, verdict="refused" if "internals" in seen else "answered")
