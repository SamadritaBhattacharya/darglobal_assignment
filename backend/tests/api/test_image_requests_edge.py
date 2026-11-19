"""'I want images of 11 bedroom villas': a photo request with listing criteria is a listing search that shows photos."""
import json

import pytest
from fastapi.testclient import TestClient

from dar.adapters.llm import ScriptedLLM
from dar.main import create_app


def listing(i, title, kind, ptype, city, district, beds, price, area, image=True):
    return {
        "id": f"w{i}", "source": "wasalt", "url": f"https://example.test/w{i}", "title": title, "section": "Listing",
        "scraped_at": "2026-11-19T10:00:00Z", "city": city, "district": district, "property_type": ptype,
        "listing_kind": kind, "price": price, "currency": "SAR", "price_period": "per year" if kind == "rent" else None,
        "area_sqm": area, "bedrooms": beds, "image_url": f"https://img.example.test/w{i}.jpg" if image else None,
        "text": f"Wasalt | {title} | Listing\n{ptype.capitalize()} for {kind} in {district}, {city}. {beds} bedrooms, {area} sqm, {price:,} SAR.\nSource: Wasalt.sa",
    }


DATA = [
    listing(1, "Villa 296 SQM with 11 Bedrooms", "rent", "villa", "Riyadh", "An-Narjis", 11, 140000, 296),
    listing(2, "Villa 250 SQM with 4 Bedrooms", "rent", "villa", "Riyadh", "Al-Yasmin", 4, 90000, 250),
    listing(3, "Apartment 120 SQM with 3 Bedrooms", "sale", "apartment", "Jeddah", "Al-Hamra", 3, 800000, 120),
    {"id": "p1", "source": "darglobal", "url": "https://example.test/neptune", "title": "Neptune", "section": "Overview",
     "scraped_at": "2026-11-18T10:00:00Z", "text": "DarGlobal | Neptune | Overview\nNeptune is a collection of villas in Riyadh by DarGlobal."},
]


@pytest.fixture(scope="module")
def setup(tmp_path_factory):
    path = tmp_path_factory.mktemp("c") / "c.json"
    path.write_text(json.dumps(DATA), encoding="utf-8")
    llm = ScriptedLLM(reply="Neptune is a collection of villas [1].")
    return TestClient(create_app(corpus_path=path, llm=llm, rate_limit_per_minute=1000)), llm


def ask(client, message):
    r = client.post("/api/chat", json={"message": message, "history": []})
    ev = [json.loads(l[6:]) for l in r.text.splitlines() if l.startswith("data: ")]
    return ev[-1]["verdict"], "".join(e["text"] for e in ev if e["type"] == "token"), next(e["sources"] for e in ev if e["type"] == "sources")


def test_the_exact_request_from_a_real_visitor_shows_the_11_bedroom_villa_with_its_photo(setup):
    client, llm = setup
    before = len(llm.received_prompts)
    verdict, text, cards = ask(client, "i want images of 11 bedroom villas")
    assert verdict == "answered"
    assert [c["url"] for c in cards] == ["https://example.test/w1"]
    assert cards[0]["image"] == "https://img.example.test/w1.jpg"
    assert "140,000 SAR per year" in text
    assert len(llm.received_prompts) == before  # free: no model call


@pytest.mark.parametrize("question, expected", [
    ("show me photos of 4 bedroom villas", ["https://example.test/w2"]),
    ("pictures of apartments for sale in Jeddah", ["https://example.test/w3"]),
    ("I want to see images of rentals in Riyadh", ["https://example.test/w1", "https://example.test/w2"]),
])
def test_photo_requests_with_listing_criteria_are_listing_searches(setup, question, expected):
    _, _, cards = ask(setup[0], question)
    assert sorted(c["url"] for c in cards) == sorted(expected)


def test_a_photo_request_for_a_bedroom_count_nobody_has_offers_the_closest(setup):
    verdict, text, cards = ask(setup[0], "images of 12 bedroom villas")
    assert verdict == "partial" and "couldn't find a 12-bedroom" in text
    assert {c["url"] for c in cards} <= {"https://example.test/w1", "https://example.test/w2"} and cards


def test_a_photo_request_about_a_project_is_not_hijacked_into_a_listing_search(setup):
    client, llm = setup
    before = len(llm.received_prompts)
    _, text, cards = ask(client, "show me images of Neptune")
    assert "matching wasalt listings" not in text.lower()
    assert cards and cards[0]["url"].endswith("/neptune")
    assert len(llm.received_prompts) == before + 1
