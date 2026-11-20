"""'What is Wasalt?' / 'Who is DarGlobal?': recognise a question that is purely about one of the two companies."""
from __future__ import annotations

import re

_COMPANY = r"(wasalt|dar\s*global)"
_TAIL = r"(?:\s+(?:company|platform|website|site|group|developer|exactly|actually))*"
_PATTERNS = [re.compile(p) for p in (
    rf"^(?:(?:what|who)\s*(?:is|'?s|are)|tell\s+me\s+(?:about|more\s+about)|explain|describe|about)\s+(?:the\s+)?{_COMPANY}{_TAIL}$",
    rf"^(?:what|how)\s+(?:does|do)\s+{_COMPANY}\s+(?:do|work)$",
    rf"^{_COMPANY}$",
)]


def which_company(message: str) -> str | None:
    """"wasalt" or "darglobal" when the whole message is an introduction question about it, else None."""
    text = re.sub(r"\s+", " ", re.sub(r"[^\w\s']", " ", message.lower())).strip()
    for pattern in _PATTERNS:
        match = pattern.match(text)
        if match:
            return "wasalt" if match.group(1) == "wasalt" else "darglobal"
    return None
