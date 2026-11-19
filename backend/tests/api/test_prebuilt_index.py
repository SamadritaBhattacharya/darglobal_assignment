"""A prebuilt index is built once (at image build time) and reused at startup; stale indexes are never trusted."""
import json
import pathlib

from fastapi.testclient import TestClient

from dar.adapters.llm import ScriptedLLM
from dar.main import build_index, create_app

FIXTURES = pathlib.Path(__file__).resolve().parents[1] / "fixtures"
REAL = FIXTURES / "corpus_realestate.json"


def top_source(client, question):
    response = client.post("/api/chat", json={"message": question, "history": []})
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]
    sources = next(e["sources"] for e in events if e["type"] == "sources")
    return sources[0]["url"].rsplit("/", 1)[-1] if sources else None


def app(corpus, index_dir=None):
    return TestClient(create_app(corpus_path=corpus, llm=ScriptedLLM(reply="ok [1]"), index_dir=index_dir))


def test_building_writes_an_index_to_disk(tmp_path):
    build_index(REAL, tmp_path / "idx")
    assert any((tmp_path / "idx").iterdir())


def test_an_app_started_from_the_prebuilt_index_answers_like_one_built_in_memory(tmp_path):
    build_index(REAL, tmp_path / "idx")
    prebuilt, fresh = app(REAL, tmp_path / "idx"), app(REAL)
    for question in ("Marlow Plaza", "family friendly neighbourhood", "4,500,000 SAR in Exampleton"):
        assert top_source(prebuilt, question) == top_source(fresh, question)


def test_a_stale_index_is_rebuilt_when_the_data_changed(tmp_path):
    build_index(REAL, tmp_path / "idx")  # index built from the old data

    changed = json.loads(REAL.read_text(encoding="utf-8"))
    for record in changed:
        if record["id"] == "re-golf":
            record["text"] = "DarGlobal | Fairway Heights | Overview\nFairway Heights now features an observatory with a giant telescope."
    new_corpus = tmp_path / "new.json"
    new_corpus.write_text(json.dumps(changed), encoding="utf-8")

    assert top_source(app(new_corpus, tmp_path / "idx"), "observatory telescope") == "golf"
