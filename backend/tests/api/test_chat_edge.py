"""Ticket 01 - walking skeleton, verified only at the chat API edge.

The single fake is the LLM network boundary (ScriptedLLM). Retrieval and the
use-case run for real.
"""
import json
import pathlib

from fastapi.testclient import TestClient

from dar.adapters.llm import ScriptedLLM
from dar.main import create_app

CORPUS = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "corpus.json"


def _chat(client: TestClient, message: str, history=None):
    response = client.post("/api/chat", json={"message": message, "history": history or []})
    assert response.status_code == 200
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]
    return events


def _client(llm=None):
    llm = llm or ScriptedLLM(reply="Alpha Residences offers two bedroom apartments [1].")
    return TestClient(create_app(corpus_path=CORPUS, llm=llm)), llm


def test_known_question_streams_an_answer_and_cites_the_right_source():
    client, _ = _client()
    events = _chat(client, "What does Alpha Residences offer?")

    text = "".join(e["text"] for e in events if e["type"] == "token")
    sources = next(e["sources"] for e in events if e["type"] == "sources")
    done = events[-1]

    assert "Alpha Residences" in text
    assert sources[0]["url"] == "https://example.test/alpha"  # the right source is cited first
    assert done["type"] == "done" and done["verdict"] == "answered"


def test_unrelated_question_still_gets_a_reply_and_no_invented_sources():
    client, llm = _client(ScriptedLLM(reply="Made up answer with no evidence."))
    events = _chat(client, "zzzz qqqq xylophone")

    text = "".join(e["text"] for e in events if e["type"] == "token")
    sources = next(e["sources"] for e in events if e["type"] == "sources")

    assert "won't guess" in text.lower()
    assert "Made up answer" not in text
    assert sources == []
    assert events[-1] == {"type": "done", "verdict": "dont_know"}
    assert llm.received_prompts == []  # no evidence -> the model is never asked to guess


def test_raw_personal_data_never_leaves_the_system():
    client, llm = _client()
    _chat(client, "My email is jane.doe@example.com, tell me about Alpha Residences")

    assert llm.received_prompts, "the model boundary was never reached"
    assert all("jane.doe@example.com" not in p for p in llm.received_prompts)


def test_overlong_message_is_rejected_with_a_client_error():
    client, _ = _client()
    response = client.post("/api/chat", json={"message": "a" * 501, "history": []})
    assert response.status_code == 422


def test_health_reports_ok_and_the_data_as_of_date():
    client, _ = _client()
    body = client.get("/api/health").json()
    assert body == {"status": "ok", "data_as_of": "2026-11-18"}
