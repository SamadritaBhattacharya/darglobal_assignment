"""What the page shows for a source: title, link, photo and one clean detail line."""
from __future__ import annotations

import re

from dar.domain.models import Chunk, SourceRef

# Navigation words scraped from the top of DarGlobal pages ("Download Brochure Book Unit Gallery ...").
_NAV_NOISE = re.compile(
    r"^(?:(?:download brochure|book unit|choose your residence|progress update|360 view|gallery|view all images|"
    r"your browser does not support the video tag\.?|overview|privacy)\s*)+",
    re.IGNORECASE,
)
CARD_DETAIL_CHARS = 180


def clean_body(chunk: Chunk) -> str:
    """The chunk text without its "Source | Title | Section" header line and without navigation noise."""
    text = chunk.text.split("\n", 1)[1] if "\n" in chunk.text else chunk.text
    text = text.replace("Source: Wasalt.sa", "")
    return _NAV_NOISE.sub("", " ".join(text.split())).strip()


def shorten(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0].rstrip(",;:- ") + "…"


def card_detail(chunk: Chunk, limit: int = CARD_DETAIL_CHARS) -> str:
    return shorten(clean_body(chunk), limit)


def source_ref(n: int, chunk: Chunk) -> SourceRef:
    return SourceRef(n=n, title=chunk.title, url=chunk.url, image=chunk.image_url, detail=card_detail(chunk))
