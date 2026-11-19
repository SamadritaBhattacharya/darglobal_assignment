"""PII redaction with an ephemeral, in-memory vault.

The vault (placeholder -> original value) exists only on the returned object.
It is never written to disk, logs or an index, and is garbage-collected with it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
_PHONE = re.compile(r"(?<![\w,.])\+?\d[\d\s\-()]{7,}\d(?!\w|[.,]\d)")


@dataclass
class Redaction:
    text: str
    _vault: dict[str, str] = field(default_factory=dict, repr=False)

    def restore(self, text: str) -> str:
        for placeholder, value in self._vault.items():
            text = text.replace(placeholder, value)
        return text


def redact(text: str) -> Redaction:
    vault: dict[str, str] = {}
    counters = {"EMAIL": 0, "PHONE": 0}
    seen: dict[tuple[str, str], str] = {}

    def placeholder(kind: str, value: str) -> str:
        key = (kind, value)
        if key not in seen:
            counters[kind] += 1
            name = f"[{kind}_{counters[kind]}]"
            seen[key] = name
            vault[name] = value
        return seen[key]

    text = _EMAIL.sub(lambda m: placeholder("EMAIL", m.group()), text)

    def phone(match: re.Match[str]) -> str:
        digits = re.sub(r"\D", "", match.group())
        if not 9 <= len(digits) <= 15:
            return match.group()
        return placeholder("PHONE", match.group())

    text = _PHONE.sub(phone, text)
    return Redaction(text=text, _vault=vault)
