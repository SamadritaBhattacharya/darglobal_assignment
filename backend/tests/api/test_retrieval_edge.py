"""Ticket 07 - hybrid retrieval, verified through the chat API by which sources come back."""
import json
import pathlib

import pytest
from fastapi.testclient import TestClient

from dar.adapters.llm import ScriptedLLM
from dar.main import create_app

CORPUS = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "corpus_realestate.json"
BASE = "https://example.test/"


@pytest.fixture(scope="module")
def client():
    return TestClient(create_app(corpus_path=CORPUS, llm=ScriptedLLM(reply="ok [1]")))


def source_urls(client, question):
    response = client.post("/api/chat", json={"message": question, "history": []})
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]
    sources = next(e["sources"] for e in events if e["type"] == "sources")
    return [s["url"].removeprefix(BASE) for s in sources]


def test_exact_project_name_finds_that_project_first(client):
    assert source_urls(client, "Marlow Plaza")[0] == "marlow"


def test_exact_price_and_place_find_the_matching_listing_first(client):
    assert source_urls(client, "4,500,000 SAR in Exampleton")[0] == "villa"


def test_paraphrase_without_shared_words_still_finds_the_right_source(client):
    assert "alpha" in source_urls(client, "cheap flat by the sea")[:3]  # 'sea' is the only shared word
    assert "garden" in source_urls(client, "good place to raise kids")[:3]  # shares no words with the page


def test_nonsense_returns_no_sources(client):
    assert source_urls(client, "quantum chromodynamics lattice gauge zzqx") == []
