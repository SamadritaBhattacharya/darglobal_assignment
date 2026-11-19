"""DarGlobal HTML page -> section chunks (pure, no network)."""
from __future__ import annotations

import re

from bs4 import BeautifulSoup, NavigableString, Tag

from dar.domain.models import Chunk
from dar.domain.pii import redact
from scraper.images import og_image

NOISE_TAGS = ["script", "style", "noscript", "svg", "header", "footer", "nav", "form", "iframe", "template"]
BOILERPLATE_HEADINGS = {
    "register your interest", "we value our privacy", "subscribe", "sign up", "cookie settings",
    "find your next investment", "related projects", "articles and news",  # search widget, link lists, dated news list
}
HEADINGS = {"h1", "h2", "h3"}
MAX_BODY_CHARS = 1500
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def _clean(text: str) -> str:
    return " ".join(text.split())


def _units(text: str) -> list[str]:
    units: list[str] = []
    for line in text.split("\n"):
        units.extend(u for u in _SENTENCE_END.split(line) if u.strip())
    return units


def _pack(units: list[str]) -> list[str]:
    """Group sentences into parts under the size limit, repeating the last sentence as overlap."""
    parts: list[list[str]] = [[]]
    size = 0
    for unit in units:
        if parts[-1] and size + len(unit) + 1 > MAX_BODY_CHARS:
            parts.append([parts[-1][-1]])
            size = len(parts[-1][0])
        parts[-1].append(unit)
        size += len(unit) + 1
    return [" ".join(p) for p in parts if p]


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "page"


def parse_page(html: str, url: str, scraped_at: str) -> list[Chunk]:
    preview_image = og_image(html)  # read before the soup strips <head> noise
    soup = BeautifulSoup(html, "lxml")
    page_title = _clean(soup.title.get_text()).split(" | ")[0] if soup.title else ""
    for tag in soup(NOISE_TAGS):
        tag.decompose()
    root = soup.body or soup

    title = page_title
    consumed = {id(t) for t in root.find_all(HEADINGS)}  # identity, not Tag equality (which compares subtrees)
    section = "Overview"
    sections: list[tuple[str, list[str]]] = [(section, [])]

    for node in root.descendants:
        if isinstance(node, Tag) and id(node) in consumed:
            text = _clean(node.get_text(" "))
            if not text:
                continue
            if node.name == "h1":
                title = title if title and sections[0][1] and False else text
            elif node.name == "h2":
                sections.append((text, []))
            else:
                sections[-1][1].append("\n" + text + "\n")
        elif isinstance(node, NavigableString):
            if any(id(p) in consumed for p in node.parents):
                continue
            text = _clean(str(node))
            if text:
                sections[-1][1].append(text)

    path_slug = _slug(url.split("darglobal.co.uk/", 1)[-1])
    chunks: list[Chunk] = []
    for ordinal, (name, pieces) in enumerate(sections, start=1):  # ordinal keeps ids unique when headings repeat
        if name.lower() in BOILERPLATE_HEADINGS:
            continue
        body = re.sub(r"[ \t]+", " ", " ".join(pieces)).replace(" \n", "\n").replace("\n ", "\n").strip()
        if not body:
            continue
        for index, part in enumerate(_pack(_units(body)), start=1):
            header = f"DarGlobal | {title or path_slug} | {name}"
            text = redact(f"{header}\n{part}").text
            chunks.append(
                Chunk(
                    id=f"darglobal:{path_slug}:{ordinal}-{_slug(name)}:{index}",
                    source="darglobal",
                    url=url,
                    title=title or path_slug,
                    section=name,
                    text=text,
                    scraped_at=scraped_at,
                    image_url=preview_image,
                )
            )
    return chunks
