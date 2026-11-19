"""The only module (besides the composition root) that knows about environment variables."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

# All support tool calling; smallest context is 262,144 tokens (OpenRouter list, 2026-11-19).
# Order = what answered in a live probe on 2026-11-19; the two Gemma models returned an upstream 429 then.
DEFAULT_MODELS = [
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "inclusionai/ling-3.2-flash:free",
    "google/gemma-4-31b-it:free",
    "google/gemma-4-26b-a4b-it:free",
]
DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "processed"
DEFAULT_STATIC_DIR = Path(__file__).resolve().parents[3] / "frontend" / "out"
DEFAULT_INDEX_DIR = Path(__file__).resolve().parents[3] / "data" / "index"


@dataclass(frozen=True)
class Settings:
    openrouter_api_key: str = field(default="", repr=False)
    models: list[str] = field(default_factory=lambda: list(DEFAULT_MODELS))
    data_dir: Path = DEFAULT_DATA_DIR
    static_dir: Path = DEFAULT_STATIC_DIR
    index_dir: Path = DEFAULT_INDEX_DIR

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> "Settings":
        models = [m.strip() for m in env.get("OPENROUTER_MODELS", "").split(",") if m.strip()]
        return cls(
            openrouter_api_key=env.get("OPENROUTER_API_KEY", ""),
            models=models or list(DEFAULT_MODELS),
            data_dir=Path(env["DATA_DIR"]) if env.get("DATA_DIR") else DEFAULT_DATA_DIR,
            static_dir=Path(env["STATIC_DIR"]) if env.get("STATIC_DIR") else DEFAULT_STATIC_DIR,
            index_dir=Path(env["INDEX_DIR"]) if env.get("INDEX_DIR") else DEFAULT_INDEX_DIR,
        )
