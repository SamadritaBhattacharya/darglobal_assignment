"""Configuration edge (environment -> settings) and the data directory edge (several files -> one corpus)."""
import json
import pathlib

from fastapi.testclient import TestClient

from dar.adapters.llm import ScriptedLLM
from dar.main import create_app
from dar.settings import Settings

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def test_defaults_give_a_free_only_model_chain_and_no_key():
    s = Settings.from_env({})
    assert s.openrouter_api_key == ""
    assert len(s.models) >= 3 and all(m.endswith(":free") for m in s.models)


def test_environment_overrides_key_models_and_data_dir():
    s = Settings.from_env({"OPENROUTER_API_KEY": "k", "OPENROUTER_MODELS": " a:free , b:free ", "DATA_DIR": "/d"})
    assert (s.openrouter_api_key, s.models, str(s.data_dir).replace("\\", "/")) == ("k", ["a:free", "b:free"], "/d")


def test_settings_never_expose_the_key_in_their_text_form():
    assert "super-secret" not in repr(Settings.from_env({"OPENROUTER_API_KEY": "super-secret"}))


def test_a_data_directory_is_loaded_as_one_corpus_and_reports_the_newest_date(tmp_path):
    for name in ("darglobal.json", "wasalt.json"):
        (tmp_path / name).write_text((FIXTURES / "corpus.json").read_text(encoding="utf-8"), encoding="utf-8")
    records = json.loads((FIXTURES / "corpus.json").read_text(encoding="utf-8"))
    # make ids unique across files, as real data is
    for name, prefix in (("darglobal.json", "d-"), ("wasalt.json", "w-")):
        data = [{**r, "id": prefix + r["id"]} for r in records]
        (tmp_path / name).write_text(json.dumps(data), encoding="utf-8")

    client = TestClient(create_app(corpus_path=tmp_path, llm=ScriptedLLM(reply="ok")))
    assert client.get("/api/health").json() == {"status": "ok", "data_as_of": "2026-11-18"}


def test_reads_a_secondary_key_and_never_reprs_it():
    s = Settings.from_env({"OPENROUTER_API_KEY": "a", "OPENROUTER_API_KEY_2": "super-secret-2"})
    assert s.openrouter_fallback_api_key == "super-secret-2"
    assert "super-secret-2" not in repr(s)
    assert Settings.from_env({}).openrouter_fallback_api_key == ""
