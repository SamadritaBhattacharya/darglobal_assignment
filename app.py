"""Entry point for Hugging Face Spaces (Gradio SDK, free tier): serves the FastAPI app on port 7860.

The Docker SDK is not available on free accounts, so the Space starts this file instead.
Secrets (OPENROUTER_API_KEY, OPENROUTER_API_KEY_2) come from the Space's environment.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "backend" / "src"))

import uvicorn  # noqa: E402

from dar.main import create_app_from_env  # noqa: E402

if __name__ == "__main__":
    uvicorn.run(create_app_from_env(), host="0.0.0.0", port=int(os.environ.get("PORT", "7860")))
