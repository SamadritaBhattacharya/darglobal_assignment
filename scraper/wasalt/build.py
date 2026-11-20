"""Turn hand-saved Wasalt listing pages into the committed dataset.

Usage: python -m scraper.wasalt.build
(Pages are saved by a human in a normal browser: Wasalt sits behind a bot check we do not bypass.)
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field
from datetime import datetime, timezone

from scraper.wasalt.home import parse_home
from scraper.wasalt.parse import parse_listing

ROOT = pathlib.Path(__file__).resolve().parents[2]
PAGES = ROOT / "data" / "raw" / "wasalt" / "pages"


@dataclass
class BuildResult:
    listings: int = 0
    about: int = 0  # the homepage description ("what is Wasalt?"), which is not a listing
    skipped: list[str] = field(default_factory=list)


def build_dataset(pages_dir: pathlib.Path, processed: pathlib.Path, export: pathlib.Path, scraped_at: str) -> BuildResult:
    result = BuildResult()
    records = {}
    for page in sorted(pathlib.Path(pages_dir).glob("*.htm*")):
        page_html = page.read_text(encoding="utf-8", errors="replace")
        chunk = parse_listing(page_html, scraped_at) or parse_home(page_html, scraped_at)
        if chunk is None:
            result.skipped.append(page.name)  # not a listing or the homepage (e.g. search results), or no usable price
        else:
            records.setdefault(chunk.id, chunk)  # the same page saved twice counts once
    result.listings = sum(1 for c in records.values() if c.price is not None)
    result.about = sum(1 for c in records.values() if c.id == "wasalt:about")

    processed.parent.mkdir(parents=True, exist_ok=True)
    export.parent.mkdir(parents=True, exist_ok=True)
    chunks = list(records.values())
    processed.write_text(json.dumps([c.model_dump(exclude_none=True) for c in chunks], indent=2, ensure_ascii=False), encoding="utf-8")
    lines = []
    for c in chunks:
        lines += [f"=== {c.title} | {c.section}", f"URL: {c.url}", f"Scraped: {c.scraped_at[:10]}", "", c.text, "", ""]
    export.write_text("\n".join(lines), encoding="utf-8")
    return result


def main() -> int:
    files = list(PAGES.glob("*.htm*"))
    stamp = max((f.stat().st_mtime for f in files), default=datetime.now(timezone.utc).timestamp())
    scraped_at = datetime.fromtimestamp(stamp, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    result = build_dataset(PAGES, ROOT / "data" / "processed" / "wasalt.json", ROOT / "data" / "export" / "wasalt.txt", scraped_at)
    print(f"{result.listings} listings + {result.about} about record built; {len(result.skipped)} pages skipped: {result.skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
