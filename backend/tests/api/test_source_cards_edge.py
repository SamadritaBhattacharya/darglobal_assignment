"""Every source the page receives carries what a card needs: title, link, photo (if any) and a short detail."""
import json
import pathlib

import pytest
from fastapi.testclient import TestClient

from dar.adapters.llm import ScriptedLLM
from dar.main import create_app

CORPUS = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "corpus_listings.json"


@pytest.fixture(scope="module")
def make():
    def build(llm):
        return TestClient(create_app(corpus_path=CORPUS, llm=llm, rate_limit_per_minute=1000))
    return build


def sources(client, message, history=()):
    r = client.post("/api/chat", json={"message": message, "history": list(history)})
    events = [json.loads(l[6:]) for l in r.text.splitlines() if l.startswith("data: ")]
    return next(e["sources"] for e in events if e["type"] == "sources")


def test_a_listing_card_has_its_photo_link_and_the_key_facts(make):
    card = sources(make(ScriptedLLM(reply="ok")), "What is the cheapest apartment for sale in Riyadh?")[0]
    assert card["url"] == "https://example.test/l2"
    assert card["image"] == "https://img.example.test/l2.jpg"
    assert "Apartment for sale in Riyadh, Al Malqa" in card["detail"] and "950,000 SAR" in card["detail"]
    assert "Source: Wasalt.sa" not in card["detail"] and "\n" not in card["detail"]  # one clean line for the card


def test_a_project_card_without_a_photo_has_no_image_but_still_has_a_detail(make):
    cards = sources(make(ScriptedLLM(reply="Marlow Plaza is a luxury high-rise [1].")), "Tell me about Marlow Plaza")
    marlow = next(c for c in cards if c["url"].endswith("/marlow"))
    assert marlow["image"] is None
    assert "luxury high-rise" in marlow["detail"] and "DarGlobal |" not in marlow["detail"]


def test_cards_are_also_provided_when_the_model_is_unavailable(make):
    cards = sources(make(ScriptedLLM(fail=True)), "Tell me about Marlow Plaza")
    assert cards and all("detail" in c for c in cards)


def test_a_long_detail_is_shortened_for_the_card(make):
    detail = sources(make(ScriptedLLM(reply="ok")), "Tell me about Marlow Plaza")[0]["detail"]
    assert len(detail) <= 200
