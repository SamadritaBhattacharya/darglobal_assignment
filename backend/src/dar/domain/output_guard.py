"""Check a model reply before the visitor sees it: it must not reveal keys, the build, or the instructions."""
from __future__ import annotations

import re

_LEAK = re.compile(
    r"sk-[A-Za-z]{0,3}-?[A-Za-z0-9\-_]{16,}|"                                   # API keys
    r"\b(?:nvidia|google|inclusionai|openai|anthropic|meta-llama)/[\w.\-:]+|"   # provider/model identifiers
    r"\b(?:nemotron|gemma|ling-3|chatgpt|gpt-?[345]|claude|gemini|llama|openrouter|langchain|langgraph|chromadb|fastapi)\b|"
    r"only the evidence|cite sources as|as data, never as instructions|system prompt|never mention 'the evidence'",
    re.IGNORECASE,
)


def leaks_internals(text: str) -> bool:
    return bool(_LEAK.search(text))
