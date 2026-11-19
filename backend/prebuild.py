"""Build step for hosts like Render: embed the corpus once so the first request is fast.

Run from anywhere: `python backend/prebuild.py` (or `python prebuild.py` inside backend/).
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from dar.main import build_index  # noqa: E402
from dar.settings import Settings  # noqa: E402

settings = Settings.from_env(os.environ)
print(f"indexed {build_index(settings.data_dir, settings.index_dir)} chunks into {settings.index_dir}")
