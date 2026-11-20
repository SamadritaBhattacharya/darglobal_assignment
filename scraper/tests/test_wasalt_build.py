"""Saved Wasalt pages -> committed dataset (processed JSON + readable txt)."""
import json

from dar.domain.models import Chunk
from scraper.tests.test_wasalt_parse import SECRET_NAME, SECRET_PHONE, page
from scraper.wasalt.build import build_dataset

HOME = '<script id="__NEXT_DATA__" type="application/json">{"props":{"pageProps":{"cmsData":{}}}}</script>'


def make(tmp_path):
    pages = tmp_path / "pages"
    pages.mkdir()
    (pages / "Apartment one.html").write_text(page(), encoding="utf-8")
    (pages / "Floor two.html").write_text(
        page({"propertyFor": "rent", "salePrice": "", "expectedRent": 45000, "slug": "floor-1-sqm-with-2-bedrooms-111"},
             top={"id": 111}), encoding="utf-8")
    (pages / "Homepage.html").write_text(HOME, encoding="utf-8")
    return pages


def run(tmp_path):
    return build_dataset(make(tmp_path), tmp_path / "wasalt.json", tmp_path / "wasalt.txt", "2026-11-19T10:00:00Z")


def test_builds_valid_records_and_reports_skipped_pages(tmp_path):
    result = run(tmp_path)
    records = json.loads((tmp_path / "wasalt.json").read_text(encoding="utf-8"))
    assert result.listings == 2 and result.skipped == ["Homepage.html"]
    assert {r["id"] for r in records} == {"wasalt:5924016", "wasalt:111"}
    for r in records:
        Chunk(**r)


def test_neither_output_file_contains_personal_details(tmp_path):
    run(tmp_path)
    for name in ("wasalt.json", "wasalt.txt"):
        body = (tmp_path / name).read_text(encoding="utf-8")
        assert SECRET_PHONE not in body and SECRET_NAME not in body


def test_txt_export_is_readable_with_url_and_attribution(tmp_path):
    run(tmp_path)
    text = (tmp_path / "wasalt.txt").read_text(encoding="utf-8")
    assert "https://wasalt.sa/en/property/sale/apartment-15278-sqm-with-5-bedrooms-5924016" in text
    assert "Source: Wasalt.sa" in text and "Scraped: 2026-11-19" in text


def test_the_homepage_adds_an_about_record_without_counting_as_a_listing(tmp_path):
    from scraper.tests.test_wasalt_home import home

    pages = make(tmp_path)
    (pages / "Homepage.html").write_text(home(), encoding="utf-8")   # replaces the empty stand-in
    result = build_dataset(pages, tmp_path / "w.json", tmp_path / "w.txt", "2026-11-19T10:00:00Z")
    records = json.loads((tmp_path / "w.json").read_text(encoding="utf-8"))
    assert result.listings == 2 and result.about == 1 and result.skipped == []
    assert "wasalt:about" in {r["id"] for r in records} and len(records) == 3


def test_the_same_listing_saved_twice_appears_once(tmp_path):
    pages = make(tmp_path)
    (pages / "Apartment one (copy).html").write_text(page(), encoding="utf-8")
    result = build_dataset(pages, tmp_path / "w.json", tmp_path / "w.txt", "2026-11-19T10:00:00Z")
    assert result.listings == 2
