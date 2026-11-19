"""The Vercel-hosted UI calls this API from another origin, so listed origins must pass CORS."""
import pathlib

from fastapi.testclient import TestClient

from dar.adapters.llm import ScriptedLLM
from dar.main import create_app

CORPUS = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "corpus.json"
ORIGIN = "https://my-ui.vercel.app"


def preflight(client, origin):
    return client.options(
        "/api/chat",
        headers={"Origin": origin, "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type"},
    )


def test_a_listed_origin_is_allowed():
    app = create_app(corpus_path=CORPUS, llm=ScriptedLLM(reply="ok"), cors_origins=[ORIGIN])
    assert preflight(TestClient(app), ORIGIN).headers["access-control-allow-origin"] == ORIGIN


def test_an_unlisted_origin_is_not_allowed():
    app = create_app(corpus_path=CORPUS, llm=ScriptedLLM(reply="ok"), cors_origins=[ORIGIN])
    assert "access-control-allow-origin" not in preflight(TestClient(app), "https://evil.example").headers


def test_no_origins_configured_means_no_cors_headers():
    app = create_app(corpus_path=CORPUS, llm=ScriptedLLM(reply="ok"))
    assert "access-control-allow-origin" not in preflight(TestClient(app), ORIGIN).headers
