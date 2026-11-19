"""Read a page's preview image (the og:image tag) from saved HTML. Pure."""
from __future__ import annotations

import html as htmllib
import re

_OG_IMAGE = re.compile(
    r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']*)["\']'
    r'|<meta[^>]+content=["\']([^"\']*)["\'][^>]+property=["\']og:image["\']',
    re.IGNORECASE,
)


def og_image(page_html: str) -> str | None:
    """The raw og:image value (HTML-unescaped), or None. Validity (https only) is enforced by the Chunk model."""
    match = _OG_IMAGE.search(page_html or "")
    if not match:
        return None
    value = htmllib.unescape(match.group(1) or match.group(2) or "").strip()
    return value or None
