"""Saved pages -> committed dataset (processed JSON + readable txt), verified by outputs."""
import json

from dar.domain.models import Chunk
from scraper.darglobal.build import build_dataset
from scraper.darglobal.fetch import cache_name

PAGE_A = "<html><title>Alpha | DG</title><body><h1>Alpha</h1><h2>Amenities</h2><p>Pool and spa.</p></body></html>"
PAGE_B = "<html><title>Beta | DG</title><body><h1>Beta</h1><p>A villa in Riyadh.</p></body></html>"
A, B = "https://darglobal.co.uk/alpha", "https://darglobal.co.uk/beta"
SITEMAP = f"<urlset><url><loc>{A}</loc></url><url><loc>{B}</loc></url><url><loc>https://darglobal.co.uk/gamma</loc></url></urlset>"


def make(tmp_path):
    pages = tmp_path / "pages"
    pages.mkdir()
    (pages / cache_name(A)).write_text(PAGE_A, encoding="utf-8")
    (pages / cache_name(B)).write_text(PAGE_B, encoding="utf-8")
    return pages  # gamma was selected but never fetched


def test_builds_valid_records_from_saved_pages_and_reports_missing_ones(tmp_path):
    out = build_dataset(SITEMAP, make(tmp_path), tmp_path / "processed.json", tmp_path / "export.txt", "2026-11-19T10:00:00Z")

    records = json.loads((tmp_path / "processed.json").read_text(encoding="utf-8"))
    assert {r["url"] for r in records} == {A, B}
    for r in records:
        Chunk(**r)
    assert out.missing == ["https://darglobal.co.uk/gamma"]
    assert out.pages == 2 and out.chunks == len(records)


def test_txt_export_is_human_readable_with_url_and_section_per_chunk(tmp_path):
    build_dataset(SITEMAP, make(tmp_path), tmp_path / "processed.json", tmp_path / "export.txt", "2026-11-19T10:00:00Z")
    text = (tmp_path / "export.txt").read_text(encoding="utf-8")
    assert A in text and "Amenities" in text and "Pool and spa." in text
    assert "Scraped: 2026-11-19" in text
