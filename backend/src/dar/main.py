"""Composition root: the only place that wires adapters to ports."""
from __future__ import annotations

import json
import os
import sys
import time
from collections.abc import Callable
from pathlib import Path

# Lets `uvicorn src.dar.main:app` work from backend/: the package imports itself as top-level `dar`.
_SRC_DIR = str(Path(__file__).resolve().parents[1])
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

from dar.adapters.catalog import InMemoryCatalog  # noqa: E402
from dar.adapters.listings import InMemoryListings  # noqa: E402
from dar.adapters.openrouter import OpenRouterLLM  # noqa: E402
from dar.adapters.retrieval import HybridRetriever  # noqa: E402
from dar.api.routes import build_router  # noqa: E402
from dar.app.answer import answer_question  # noqa: E402
from dar.domain.models import ChatRequest, Chunk  # noqa: E402
from dar.domain.ports import LLM  # noqa: E402
from dar.domain.ratelimit import SlidingWindowLimiter  # noqa: E402
from dar.settings import Settings  # noqa: E402


def load_corpus(path: Path) -> list[Chunk]:
    path = Path(path)
    files = sorted(path.glob("*.json")) if path.is_dir() else [path]
    return [Chunk(**record) for f in files for record in json.loads(f.read_text(encoding="utf-8"))]


def create_app(
    corpus_path: Path,
    llm: LLM,
    rate_limit_per_minute: int = 20,
    clock: Callable[[], float] = time.monotonic,
    static_dir: Path | None = None,
    index_dir: Path | None = None,
    cors_origins: list[str] | None = None,
) -> FastAPI:
    chunks = load_corpus(corpus_path)
    retriever = HybridRetriever(chunks, index_dir=index_dir)
    listings = InMemoryListings(chunks)
    catalog = InMemoryCatalog(chunks)
    data_as_of = max((c.scraped_at[:10] for c in chunks), default=None)

    def answer(request: ChatRequest):
        return answer_question(request, retriever, llm, listings, catalog)

    app = FastAPI(title="DarGlobal & Wasalt assistant")
    if cors_origins:
        app.add_middleware(CORSMiddleware, allow_origins=cors_origins, allow_methods=["POST", "GET"], allow_headers=["*"])
    app.include_router(build_router(answer, data_as_of, SlidingWindowLimiter(rate_limit_per_minute, clock)))
    if static_dir is not None and Path(static_dir).is_dir():
        # mounted last so every /api route above takes precedence
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="site")
    return app


def build_index(corpus_path: Path, index_dir: Path) -> int:
    """Embed the corpus once and persist the vectors (run at image build time). Returns the chunk count."""
    chunks = load_corpus(corpus_path)
    HybridRetriever(chunks, index_dir=index_dir)
    return len(chunks)


def _load_dotenv(path: Path) -> None:
    """Dev convenience: read KEY=VALUE lines from the repo-root .env without overriding real env vars."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def create_app_from_env() -> FastAPI:
    """Builds the app from the environment (and the repo-root .env, if present)."""
    _load_dotenv(Path(__file__).resolve().parents[3] / ".env")
    settings = Settings.from_env(os.environ)
    return create_app(
        settings.data_dir,
        OpenRouterLLM(
            settings.openrouter_api_key, settings.models, fallback_api_key=settings.openrouter_fallback_api_key
        ),
        static_dir=settings.static_dir,
        index_dir=settings.index_dir,
        cors_origins=settings.cors_origins,
    )


_app: FastAPI | None = None


def __getattr__(name: str):
    """Lazy module-level `app` so `uvicorn src.dar.main:app` works; importing this module stays side-effect free."""
    global _app
    if name == "app":
        if _app is None:
            _app = create_app_from_env()
        return _app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


if __name__ == "__main__":  # `python -m dar.main` builds the index (used by the Dockerfile)
    _settings = Settings.from_env(os.environ)
    print(f"indexed {build_index(_settings.data_dir, _settings.index_dir)} chunks into {_settings.index_dir}")
