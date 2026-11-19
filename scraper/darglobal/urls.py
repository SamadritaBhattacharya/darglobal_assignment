"""Choose which DarGlobal pages to scrape from the sitemap (pure function)."""
from __future__ import annotations

import html
import re

HOST = "https://darglobal.co.uk"
_LOC = re.compile(re.escape(HOST) + r"/[^\s<\"']*")

GROUP_PREFIXES = ("projects", "partners", "one-of-one", "rayana", "amaya", "trump-plaza")
SAMPLED = {"press": 8, "insights": 5}

# Top-level pages that are not property or information content.
EXCLUDED_TOP_LEVEL = {
    "blog", "press", "insights", "projects", "partners", "one-of-one", "pay-online", "careers", "thank-you",
    "success", "become-a-broker", "become-an-agent", "internships", "internship-application", "landingpage",
    "landing-page", "bookyourunit", "privacy-policy", "terms-conditions", "terms-of-uses", "new-home-page",
    "campaigns", "get-in-touch", "win-a-trip-to-dubai", "broker-contest-terms-conditions", "sohar-islamic",
    "aston-martin-media", "dg-circle", "darglobal-insignia-card", "invest-crypto",
}


def _path(url: str) -> str:
    return url[len(HOST):].strip("/")


def select_urls(sitemap_text: str) -> list[str]:
    seen: set[str] = set()
    taken = {name: 0 for name in SAMPLED}
    chosen: list[str] = []
    for raw in _LOC.findall(html.unescape(sitemap_text)):
        path = _path(raw)
        key = path.lower()
        if not path or key in seen:
            continue
        seen.add(key)
        parts = key.split("/")
        head = parts[0]
        if head in SAMPLED and len(parts) > 1:
            if taken[head] >= SAMPLED[head]:
                continue
            taken[head] += 1
        elif head in GROUP_PREFIXES:
            if len(parts) == 1:
                continue
        elif head in EXCLUDED_TOP_LEVEL or head == "blog" or len(parts) > 1:
            continue
        chosen.append(f"{HOST}/{path}")
    return chosen
