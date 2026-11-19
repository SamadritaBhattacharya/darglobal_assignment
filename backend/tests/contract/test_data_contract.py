"""Data-contract edge: what is allowed to enter data/processed and the index."""
import json
import pathlib

import pytest
from pydantic import ValidationError

from dar.domain.models import Chunk

FIXTURE = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "corpus.json"
PROCESSED = pathlib.Path(__file__).resolve().parents[3] / "data" / "processed"

BASE = dict(
    id="x1", source="wasalt", url="https://example.test/x", title="T", section="S",
    text="Apartment in Riyadh, 3 bedrooms, 1,200,000 SAR", scraped_at="2026-11-18T10:00:00Z",
)


def test_fixture_records_are_valid():
    for record in json.loads(FIXTURE.read_text(encoding="utf-8")):
        Chunk(**record)


def test_record_with_an_email_in_any_text_field_is_rejected():
    with pytest.raises(ValidationError):
        Chunk(**{**BASE, "text": "Contact agent at agent@example.com"})
    with pytest.raises(ValidationError):
        Chunk(**{**BASE, "title": "Owner jane@example.com"})


def test_record_with_a_phone_number_is_rejected():
    with pytest.raises(ValidationError):
        Chunk(**{**BASE, "text": "Call +966 50 123 4567 to view"})


def test_record_without_url_or_timestamp_is_rejected():
    with pytest.raises(ValidationError):
        Chunk(**{k: v for k, v in BASE.items() if k != "url"})
    with pytest.raises(ValidationError):
        Chunk(**{k: v for k, v in BASE.items() if k != "scraped_at"})


def test_normal_prices_and_areas_pass():
    Chunk(**{**BASE, "text": "Price 2500000 SAR, area 350 sqm, 4 bedrooms"})


def test_every_committed_processed_file_is_valid_and_pii_free():
    if not PROCESSED.exists():
        pytest.skip("no processed data yet")
    for path in PROCESSED.glob("*.json"):
        for record in json.loads(path.read_text(encoding="utf-8")):
            Chunk(**record)
