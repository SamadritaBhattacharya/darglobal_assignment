"""Ticket 12 - the 'I don't know' gate on real data, observed at the chat API edge."""
import json
import pathlib

import pytest
from fastapi.testclient import TestClient

from dar.adapters.llm import ScriptedLLM
from dar.main import create_app

DATA = pathlib.Path(__file__).resolve().parents[3] / "data" / "processed" / "darglobal.json"
pytestmark = pytest.mark.skipif(not DATA.exists(), reason="no processed DarGlobal data")


@pytest.fixture(scope="module")
def setup():
    llm = ScriptedLLM(reply="Grounded answer [1].")
    return TestClient(create_app(corpus_path=DATA, llm=llm)), llm


def ask(client, question):
    response = client.post("/api/chat", json={"message": question, "history": []})
    return [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]


@pytest.mark.parametrize(
    "question",
    [
        "What is the weather in Paris today?",
        "Write me a poem about cats",
        "Who won the football world cup in 2018?",
        "How do I bake sourdough bread?",
        "What is the capital of Australia?",
    ],
)
def test_off_topic_questions_get_dont_know_and_the_model_is_never_asked(setup, question):
    client, llm = setup
    before = len(llm.received_prompts)
    events = ask(client, question)
    assert events[-1] == {"type": "done", "verdict": "dont_know"}
    assert len(llm.received_prompts) == before


@pytest.mark.parametrize(
    "question",
    ["Where is Neptune located?", "Tell me about Trump Tower Jeddah", "What amenities does Les Vagues have?"],
)
def test_real_questions_are_still_answered(setup, question):
    client, _ = setup
    assert ask(client, question)[-1] == {"type": "done", "verdict": "answered"}
