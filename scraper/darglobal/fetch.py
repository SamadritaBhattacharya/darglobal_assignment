"""Polite DarGlobal fetcher (offline tool, run by a human).

One page at a time, human pace, cached, robots.txt-aware. If a bot challenge appears it
STOPS and reports; it never tries to get around it (fallback: save pages by hand, see README).

Usage: python -m scraper.darglobal.fetch
"""
from __future__ import annotations

import hashlib
import pathlib
import time
import urllib.robotparser

from playwright.sync_api import sync_playwright

from scraper.darglobal.urls import HOST, select_urls

ROOT = pathlib.Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "darglobal"
PAGES = RAW / "pages"
DELAY_SECONDS = 4.0
CHALLENGE_MARK = "_Incapsula_Resource"


class ChallengeDetected(RuntimeError):
    pass


def cache_name(url: str) -> str:
    slug = url.removeprefix(HOST + "/").strip("/").replace("/", "__") or "home"
    return f"{slug}-{hashlib.sha1(url.encode()).hexdigest()[:6]}.html"


def _visit(page, url: str) -> str:
    page.goto(url, wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(2500)
    body = page.content()
    if CHALLENGE_MARK in body and len(body) < 5000:
        raise ChallengeDetected(url)
    return body


def main() -> int:
    PAGES.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_context(locale="en-GB", viewport={"width": 1366, "height": 900}).new_page()
        try:
            robots = urllib.robotparser.RobotFileParser()
            robots.parse(_visit(page, f"{HOST}/robots.txt").splitlines())
            sitemap = RAW / "sitemap_rendered.xml"
            if not sitemap.exists():
                sitemap.write_text(_visit(page, f"{HOST}/sitemap.xml"), encoding="utf-8")
            urls = select_urls(sitemap.read_text(encoding="utf-8"))
            done = skipped = 0
            for url in urls:
                target = PAGES / cache_name(url)
                if target.exists():
                    continue
                if not robots.can_fetch("*", url):
                    skipped += 1
                    print("robots disallows, skipped:", url)
                    continue
                target.write_text(_visit(page, url), encoding="utf-8")
                done += 1
                print(f"[{done}] saved {url}")
                time.sleep(DELAY_SECONDS)
            print(f"finished: {done} new, {skipped} skipped by robots, {len(urls)} selected")
            return 0
        except ChallengeDetected as err:
            print("STOPPED: bot challenge detected at", err, "- not bypassing. Use the manual-save fallback.")
            return 2
        finally:
            browser.close()


if __name__ == "__main__":
    raise SystemExit(main())
