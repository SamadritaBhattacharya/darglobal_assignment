---
title: DarGlobal Assistant
emoji: 🏢
colorFrom: indigo
colorTo: blue
sdk: gradio
sdk_version: 5.49.1
app_file: app.py
python_version: 3.11.13
pinned: false
---

# DarGlobal & Wasalt assistant

A grounded chatbot over public DarGlobal and Wasalt data. FastAPI backend (`backend/`) serving a statically exported Next.js UI (`frontend/`) from one container on port 7860.

Run locally: from `backend/`, `uvicorn src.dar.main:app --reload --port 8000` (after `npm run build` in `frontend/`).
Deploy: Hugging Face Spaces (Gradio SDK runs `app.py`, which serves the FastAPI backend; the Docker SDK is paid). Set `OPENROUTER_API_KEY` (and optionally `OPENROUTER_API_KEY_2`) as Space secrets.
