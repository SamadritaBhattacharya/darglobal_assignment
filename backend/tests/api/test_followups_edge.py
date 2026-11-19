"""Ticket 10 (backend half) - conversation follow-ups, observed at the chat API edge."""
import json
import pathlib

import pytest
from fastapi.testclient import TestClient

from dar.adapters.llm import ScriptedLLM
from dar.main import create_app

CORPUS = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "corpus_realestate.json"


@pytest.fixture(scope="module")
def setup():
    llm = ScriptedLLM(reply="Fine [1].")
    return TestClient(create_app(corpus_path=CORPUS, llm=llm, rate_limit_per_minute=1000)), llm


def chat(client, message, history=()):
    response = client.post("/api/chat", json={"message": message, "history": list(history)})
    assert response.status_code == 200, response.text
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]
    return [s["url"].rsplit("/", 1)[-1] for s in next(e["sources"] for e in events if e["type"] == "sources")]


def test_a_pronoun_follow_up_is_answered_from_the_previous_subject(setup):
    client, _ = setup
    history = [
        {"role": "user", "content": "Tell me about the villa in Exampleton"},
        {"role": "assistant", "content": "It is a five bedroom villa with a private garden [1]."},
    ]
    assert chat(client, "And how much does it cost?", history)[0] == "villa"


def test_a_new_standalone_question_is_not_dragged_back_to_the_old_topic(setup):
    client, _ = setup
    history = [
        {"role": "user", "content": "Tell me about the villa in Exampleton"},
        {"role": "assistant", "content": "It is a five bedroom villa [1]."},
    ]
    assert chat(client, "Tell me about Marlow Plaza executive residences", history)[0] == "marlow"


def test_a_very_long_history_still_succeeds_and_keeps_the_most_recent_turns(setup):
    client, llm = setup
    history = []
    for i in range(60):
        history.append({"role": "user", "content": f"turn-{i} " + "filler " * 400})
        history.append({"role": "assistant", "content": f"reply-{i} " + "filler " * 400})
    history.append({"role": "user", "content": "LAST-MARKER tell me about Marlow Plaza"})

    before = len(llm.received_prompts)
    chat(client, "Marlow Plaza please", history[-100:])
    prompt = llm.received_prompts[before]
    assert "LAST-MARKER" in prompt
    assert "turn-0 " not in prompt  # the oldest turns were trimmed away
    assert len(prompt) < 14000  # bounded by the history budget, not by the visitor's scrolling


def test_history_larger_than_the_hard_limit_is_rejected_not_crashed(setup):
    client, _ = setup
    too_many = [{"role": "user", "content": "x"}] * 101
    assert client.post("/api/chat", json={"message": "hi", "history": too_many}).status_code == 422
