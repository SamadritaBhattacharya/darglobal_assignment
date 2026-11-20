"""The Wasalt homepage's own description -> an "About Wasalt" record (pure, no network).

Only the real homepage qualifies. Wasalt's search-result and category pages are skipped on purpose: its AI policy
asks that internal search results are not scraped or replicated.
"""
from __future__ import annotations

import html as htmllib
import re

from pydantic import ValidationError

from dar.domain.models import Chunk
from scraper.images import og_image

HOME_URL = "https://wasalt.sa/en"
_CANONICAL = re.compile(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']|<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']canonical["\']', re.IGNORECASE)
_DESCRIPTION = re.compile(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)["\']|<meta[^>]+content=["\']([^"\']*)["\'][^>]+name=["\']description["\']', re.IGNORECASE)


def parse_home(page_html: str, scraped_at: str) -> Chunk | None:
    canonical = _CANONICAL.search(page_html or "")
    if not canonical or (canonical.group(1) or canonical.group(2)).rstrip("/") != HOME_URL:
        return None
    if '"propertyDetailsV3"' in page_html:
        return None
    found = _DESCRIPTION.search(page_html)
    description = htmllib.unescape((found.group(1) or found.group(2) or "") if found else "").strip()
    description = re.sub(r"\s*\|\s*Wasalt\s*$", "", description)        # drop the site-name suffix
    description = re.sub(r"(?<=[a-z])\.(?=[A-Z])", ". ", description)   # "properties.Installment" -> "properties. Installment"
    if not description:
        return None
    try:
        return Chunk(
            id="wasalt:about", source="wasalt", url=HOME_URL, title="About Wasalt", section="Overview",
            text=f"Wasalt | About Wasalt | Overview\n{description}\nSource: Wasalt.sa",
            scraped_at=scraped_at, image_url=og_image(page_html),
        )
    except ValidationError:
        return None
