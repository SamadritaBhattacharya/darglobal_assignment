"""One container, one URL: the API and the exported UI are served together."""
import pathlib

from fastapi.testclient import TestClient

from dar.adapters.llm import ScriptedLLM
from dar.main import create_app

CORPUS = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "corpus.json"


def site(tmp_path):
    (tmp_path / "index.html").write_text("<html><body>Hello assistant</body></html>", encoding="utf-8")
    (tmp_path / "_next").mkdir()
    (tmp_path / "_next" / "app.js").write_text("console.log('ok')", encoding="utf-8")
    return TestClient(create_app(corpus_path=CORPUS, llm=ScriptedLLM(reply="ok"), static_dir=tmp_path))


def test_the_home_page_and_its_assets_are_served(tmp_path):
    client = site(tmp_path)
    home = client.get("/")
    assert home.status_code == 200 and "Hello assistant" in home.text
    assert client.get("/_next/app.js").status_code == 200


def test_the_api_still_answers_beside_the_site(tmp_path):
    client = site(tmp_path)
    assert client.get("/api/health").json()["status"] == "ok"
    assert client.post("/api/chat", json={"message": "Alpha Residences", "history": []}).status_code == 200


def test_unknown_pages_are_a_plain_404_and_unknown_api_routes_are_not_swallowed(tmp_path):
    client = site(tmp_path)
    assert client.get("/nope").status_code == 404
    assert client.get("/api/nope").status_code == 404


def test_the_app_runs_without_a_built_site(tmp_path):
    client = TestClient(create_app(corpus_path=CORPUS, llm=ScriptedLLM(reply="ok"), static_dir=tmp_path / "missing"))
    assert client.get("/api/health").status_code == 200
    assert client.get("/").status_code == 404
