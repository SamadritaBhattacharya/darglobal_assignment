"""Small talk: a good chatbot greets back, says what it can do, and never treats 'hi' as a failed search."""
import json
import pathlib

import pytest
from fastapi.testclient import TestClient

from dar.adapters.llm import ScriptedLLM
from dar.main import create_app

CORPUS = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "corpus.json"


@pytest.fixture(scope="module")
def setup():
    llm = ScriptedLLM(reply="Alpha Residences offers two bedroom apartments [1].")
    return TestClient(create_app(corpus_path=CORPUS, llm=llm, rate_limit_per_minute=1000)), llm


def chat(client, message):
    r = client.post("/api/chat", json={"message": message, "history": []})
    events = [json.loads(l[6:]) for l in r.text.splitlines() if l.startswith("data: ")]
    text = "".join(e["text"] for e in events if e["type"] == "token")
    sources = next(e["sources"] for e in events if e["type"] == "sources")
    return events[-1]["verdict"], text, sources


@pytest.mark.parametrize("message", ["hi", "Hi!", "hello", "Hello there", "hey", "Good morning", "good evening!", "hiya", "Hi, assistant"])
def test_a_greeting_is_greeted_back_and_the_visitor_is_shown_what_to_ask(setup, message):
    client, llm = setup
    before = len(llm.received_prompts)
    verdict, text, sources = chat(client, message)
    assert verdict == "answered" and sources == []
    assert text.lower().startswith(("hi", "hello", "hey", "good"))
    assert "darglobal" in text.lower() and "wasalt" in text.lower()
    assert text.count("?") >= 2  # example questions to try
    assert "couldn't find" not in text.lower() and "won't guess" not in text.lower()
    assert len(llm.received_prompts) == before  # no model call needed


@pytest.mark.parametrize("message", ["thanks", "Thank you!", "thank you so much", "thx"])
def test_thanks_gets_a_friendly_reply(setup, message):
    verdict, text, _ = chat(setup[0], message)
    assert verdict == "answered" and "welcome" in text.lower()


@pytest.mark.parametrize("message", ["bye", "Goodbye!", "see you"])
def test_a_goodbye_gets_a_goodbye(setup, message):
    verdict, text, _ = chat(setup[0], message)
    assert verdict == "answered" and any(w in text.lower() for w in ("bye", "take care", "see you"))


@pytest.mark.parametrize("message", ["how are you", "How are you?", "what can you do", "who are you", "help", "What do you know?"])
def test_questions_about_the_assistant_itself_are_answered_helpfully(setup, message):
    verdict, text, _ = chat(setup[0], message)
    assert verdict == "answered"
    assert "darglobal" in text.lower() and "wasalt" in text.lower()
    assert "couldn't find" not in text.lower()


def test_a_greeting_followed_by_a_real_question_is_still_a_real_question(setup):
    client, llm = setup
    before = len(llm.received_prompts)
    verdict, text, sources = chat(client, "Hi, tell me about Alpha Residences")
    assert sources and sources[0]["url"] == "https://example.test/alpha"
    assert len(llm.received_prompts) == before + 1  # went down the normal path
