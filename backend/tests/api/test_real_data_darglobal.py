"""Ticket 05 acceptance: real DarGlobal data answers five hand-picked questions with the right source.

Skipped when the committed dataset is absent. Only retrieval outcomes are asserted (sources), via the chat API.
"""
import json
import pathlib

import pytest
from fastapi.testclient import TestClient

from dar.adapters.llm import ScriptedLLM
from dar.main import create_app

DATA = pathlib.Path(__file__).resolve().parents[3] / "data" / "processed" / "darglobal.json"
pytestmark = pytest.mark.skipif(not DATA.exists(), reason="no processed DarGlobal data")


@pytest.fixture(scope="module")
def client():
    return TestClient(create_app(corpus_path=DATA, llm=ScriptedLLM(reply="ok [1]")))


def top_urls(client, question, n=3):
    response = client.post("/api/chat", json={"message": question, "history": []})
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]
    return [s["url"].lower() for s in next(e["sources"] for e in events if e["type"] == "sources")][:n]


@pytest.mark.parametrize(
    "question, expected_fragment",
    [
        ("Who designed the interiors of Neptune in Riyadh?", "neptune"),
        ("Tell me about Trump Tower Jeddah", "trump-tower-jeddah"),
        ("What is Les Vagues by Elie Saab?", "les-vagues"),
        ("Which tower is designed by Pagani?", "pagani"),
        ("Azure oceanfront villas by Fendi Casa in Oman", "fendi"),
    ],
)
def test_real_question_surfaces_the_right_page_in_the_top_three(client, question, expected_fragment):
    assert any(expected_fragment in url for url in top_urls(client, question)), top_urls(client, question)
