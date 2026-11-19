"""Turn saved DarGlobal pages into the committed dataset.

Usage: python -m scraper.darglobal.build
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field
from datetime import datetime, timezone

from scraper.darglobal.fetch import PAGES, RAW, cache_name
from scraper.darglobal.parse import parse_page
from scraper.darglobal.urls import select_urls

ROOT = pathlib.Path(__file__).resolve().parents[2]


@dataclass
class BuildResult:
    pages: int = 0
    chunks: int = 0
    missing: list[str] = field(default_factory=list)


def build_dataset(sitemap_text: str, pages_dir: pathlib.Path, processed: pathlib.Path,
                  export: pathlib.Path, scraped_at: str) -> BuildResult:
    result = BuildResult()
    records = []
    for url in select_urls(sitemap_text):
        saved = pages_dir / cache_name(url)
        if not saved.exists():
            result.missing.append(url)
            continue
        result.pages += 1
        records.extend(parse_page(saved.read_text(encoding="utf-8"), url, scraped_at))
    result.chunks = len(records)

    processed.parent.mkdir(parents=True, exist_ok=True)
    export.parent.mkdir(parents=True, exist_ok=True)
    processed.write_text(
        json.dumps([r.model_dump(exclude_none=True) for r in records], indent=2, ensure_ascii=False), encoding="utf-8"
    )
    lines = []
    for r in records:
        lines += [f"=== {r.title} | {r.section}", f"URL: {r.url}", f"Scraped: {r.scraped_at[:10]}", "", r.text, "", ""]
    export.write_text("\n".join(lines), encoding="utf-8")
    return result


def main() -> int:
    sitemap = (RAW / "sitemap_rendered.xml").read_text(encoding="utf-8")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    result = build_dataset(sitemap, PAGES, ROOT / "data" / "processed" / "darglobal.json",
                           ROOT / "data" / "export" / "darglobal.txt", now)
    print(f"{result.pages} pages -> {result.chunks} chunks; {len(result.missing)} selected pages not fetched")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
