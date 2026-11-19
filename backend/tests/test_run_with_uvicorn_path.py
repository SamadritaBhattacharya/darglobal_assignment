"""`uvicorn src.dar.main:app` (run from backend/) must resolve a ready-to-serve ASGI app."""
import os
import pathlib
import subprocess
import sys

BACKEND = pathlib.Path(__file__).resolve().parents[1]


def test_src_dar_main_app_is_importable_from_backend_dir():
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    code = "import src.dar.main as m; print(m.app.title)"
    result = subprocess.run(
        [sys.executable, "-c", "import sys; sys.path.insert(0, '.'); import src.dar.main as m; print(m.app.title)"],
        cwd=BACKEND, env=env, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "DarGlobal" in result.stdout
