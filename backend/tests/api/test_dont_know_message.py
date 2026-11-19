"""What a visitor reads when the bot has no grounded answer: honest, helpful, no invented facts."""
import json
import pathlib

import pytest
from fastapi.testclient import TestClient

from dar.adapters.llm import ScriptedLLM
from dar.main import create_app

CORPUS = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "corpus.json"


@pytest.fixture(scope="module")
def reply():
    client = TestClient(create_app(corpus_path=CORPUS, llm=ScriptedLLM(reply="should never be used")))
    response = client.post("/api/chat", json={"message": "zzzz qqqq xylophone", "history": []})
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]
    return {"verdict": events[-1]["verdict"], "text": "".join(e["text"] for e in events if e["type"] == "token")}


def test_says_plainly_that_it_could_not_find_this_and_will_not_guess(reply):
    assert reply["verdict"] == "dont_know"
    assert "couldn't find" in reply["text"].lower()
    assert "won't guess" in reply["text"].lower()


def test_explains_what_the_assistant_can_help_with(reply):
    text = reply["text"].lower()
    assert "darglobal" in text and "wasalt" in text
    assert any(word in text for word in ("projects", "listings"))


def test_offers_example_questions_to_try_next(reply):
    assert reply["text"].count("?") >= 2


def test_points_to_the_live_sites_for_current_information(reply):
    assert "darglobal.co.uk" in reply["text"] and "wasalt.sa" in reply["text"]


def test_is_short_enough_to_read_at_a_glance(reply):
    assert len(reply["text"]) <= 700
