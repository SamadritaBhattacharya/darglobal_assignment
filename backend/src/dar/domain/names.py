"""The visitor's name: recognised in their messages, validated hard, kept only in their own browser."""
from __future__ import annotations

import re

from dar.domain.greetings import strip_greeting
from dar.domain.guardrails import check as _looks_hostile

_TOKEN = re.compile(r"[A-Za-z][A-Za-z'’\-]{1,24}")
_BLOCKED = {
    "ignore", "instructions", "instruction", "previous", "system", "prompt", "assistant", "admin", "administrator",
    "developer", "root", "bot", "ai", "claude", "gpt", "chatgpt", "openai", "anthropic", "gemini", "llama", "null",
    "undefined", "none", "true", "false", "user", "me", "you", "unknown", "test", "darglobal", "wasalt",
}
# Words that follow "I am ..." in ordinary sentences and are not names.
_NOT_NAMES = _BLOCKED | {
    "interested", "looking", "from", "here", "happy", "fine", "good", "great", "sure", "new", "not", "just", "also",
    "planning", "going", "trying", "wondering", "curious", "ok", "okay", "sorry", "glad", "excited", "student",
    "buyer", "investor", "agent", "ready", "back", "thinking", "hoping", "searching", "wanting", "needing",
    "hungry", "tired", "thirsty", "busy", "bored", "lost", "confused", "late", "early", "online", "offline", "sick",
    "ill", "angry", "sad", "lonely", "afraid", "scared", "nervous", "worried", "stuck", "rich", "poor", "single",
    "married", "retired", "unemployed", "teacher", "engineer", "doctor", "developer", "owner", "tenant", "landlord",
    "broker", "visitor", "customer", "client", "guest", "here", "there", "well", "alright", "free", "available",
    "interested", "looking", "wondering", "happy", "excited", "glad", "sorry", "sure", "new",
}
_LOWERCASE_IMPLICIT = re.compile(r"^(?i:i\s+am|i'?m|im|this\s+is)\s+([A-Za-z][A-Za-z'’\-]{1,24})$")
_STOP_AFTER_NAME = {"and", "but", "from", "i", "im", "i'm", "is", "can", "could", "please", "what", "who", "how",
                    "where", "when", "why", "do", "does", "are", "am", "the", "a", "an", "so", "then", "thanks", "thank"}
_EXPLICIT = re.compile(
    r"\b(?:my\s+name\s+is|my\s+name'?s|i\s+am\s+called|i'?m\s+called|call\s+me|you\s+can\s+call\s+me|people\s+call\s+me|name'?s)\s+"
    r"([A-Za-z][A-Za-z'’\-]{1,24}(?:\s+[A-Za-z][A-Za-z'’\-]{1,24}){0,3})",
    re.IGNORECASE,
)
# "I am Samadrita": the introduction words are matched in any case, but the name itself must be capitalised.
_IMPLICIT = re.compile(r"^(?i:i\s+am|i'?m|im|this\s+is)\s+([A-Z][A-Za-z'’\-]{1,24})$")


def valid_name(raw: str | None) -> str | None:
    """A safe display name, or None. Letters only, at most 3 words, nothing that looks like an attack or a role."""
    if not raw:
        return None
    text = " ".join(raw.split())
    tokens = text.split(" ")
    if len(text) > 40 or not 1 <= len(tokens) <= 3 or any(not _TOKEN.fullmatch(t) for t in tokens):
        return None
    if any(t.lower().strip("'’-") in _BLOCKED for t in tokens) or _looks_hostile(text):
        return None
    return " ".join(t.capitalize() if t.islower() or t.isupper() else t for t in tokens)


def _sentences(message: str) -> list[str]:
    return [s.strip() for s in re.split(r"[.!?\n]+", message) if s.strip()]


def extract_name(message: str) -> str | None:
    """The name the visitor just gave ("my name is Sam", "I am Samadrita"), or None."""
    for sentence in _sentences(message):
        explicit = _EXPLICIT.search(sentence)
        if explicit:
            words: list[str] = []
            for word in explicit.group(1).split():
                if word.lower() in _STOP_AFTER_NAME:
                    break
                words.append(word)
            name = valid_name(" ".join(words))
            if name:
                return name
        implicit = _IMPLICIT.match(sentence)
        if implicit and implicit.group(1).lower() not in _NOT_NAMES:
            name = valid_name(implicit.group(1))
            if name:
                return name
        # "hi i am samadrita": straight after a greeting a lowercase name is clear enough, unless it is an ordinary word
        greeted, rest = strip_greeting(sentence)
        relaxed = _LOWERCASE_IMPLICIT.match(rest) if greeted and rest else None
        if relaxed:
            token = relaxed.group(1)
            if token.lower() not in _NOT_NAMES and not token.lower().endswith(("ing", "ed")):
                name = valid_name(token)
                if name:
                    return name
    return None
