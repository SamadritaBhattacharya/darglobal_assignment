"""'Open the 1st one', 'show the image of the second one': follow-ups that pick one of the results just shown."""
import json
import pathlib

import pytest
from fastapi.testclient import TestClient

from dar.adapters.llm import ScriptedLLM
from dar.main import create_app

CORPUS = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "corpus_listings.json"
L6 = {"n": 1, "title": "Apartment for rent, Al Yasmin, Riyadh", "url": "https://example.test/l6"}
L2 = {"n": 2, "title": "Apartment for sale, Al Malqa, Riyadh", "url": "https://example.test/l2"}


@pytest.fixture(scope="module")
def setup():
    llm = ScriptedLLM(reply="Marlow Plaza is a luxury high-rise [1].")
    return TestClient(create_app(corpus_path=CORPUS, llm=llm, rate_limit_per_minute=1000)), llm


def shown(*sources):
    return [{"role": "user", "content": "rentals in Riyadh"},
            {"role": "assistant", "content": "Here are the matching listings.", "sources": list(sources)}]


def pick(client, message, history):
    r = client.post("/api/chat", json={"message": message, "history": history})
    assert r.status_code == 200, r.text
    ev = [json.loads(l[6:]) for l in r.text.splitlines() if l.startswith("data: ")]
    return ev[-1]["verdict"], "".join(e["text"] for e in ev if e["type"] == "token"), next(e["sources"] for e in ev if e["type"] == "sources")


@pytest.mark.parametrize("message", ["open the 1st one", "Show me the first one", "I want to see the first listing", "details of the 1st one"])
def test_picking_the_first_result_shows_its_details_photo_and_link(setup, message):
    client, llm = setup
    before = len(llm.received_prompts)
    verdict, text, cards = pick(client, message, shown(L6, L2))
    assert verdict == "answered"
    assert [c["url"] for c in cards] == ["https://example.test/l6"]
    assert cards[0]["image"] == "https://img.example.test/l6.jpg"
    assert "Al Yasmin" in text and "45,000 SAR per year" in text and "2 bedrooms" in text and "95 sqm" in text
    assert "button" in text.lower()  # tells the visitor how to open the full page
    assert len(llm.received_prompts) == before  # free: no model call


@pytest.mark.parametrize("message", ["show me the image of the second one", "open the 2nd result", "the second one please", "number 2"])
def test_other_ordinals_pick_the_matching_result(setup, message):
    assert pick(setup[0], message, shown(L6, L2))[2][0]["url"] == "https://example.test/l2"


def test_asking_for_the_image_when_only_one_result_was_shown_means_that_one(setup):
    assert pick(setup[0], "I want to see the image", shown(L6))[2][0]["url"] == "https://example.test/l6"


def test_picking_a_number_beyond_what_was_shown_explains_how_many_there_were(setup):
    verdict, text, cards = pick(setup[0], "open the 5th one", shown(L6, L2))
    assert verdict == "answered" and cards == []
    assert "2 results" in text


def test_picking_before_anything_was_shown_explains_what_to_do(setup):
    verdict, text, cards = pick(setup[0], "open the 1st one", [])
    assert verdict == "answered" and cards == []
    assert "rentals in Riyadh" in text or "ask me" in text.lower()


def test_an_ordinary_question_that_merely_contains_a_number_word_is_not_a_pick(setup):
    client, llm = setup
    before = len(llm.received_prompts)
    _, _, cards = pick(client, "Tell me about the first floor of Marlow Plaza", shown(L6, L2))
    assert cards and cards[0]["url"].endswith("/marlow")
    assert len(llm.received_prompts) == before + 1  # normal path
