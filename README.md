---
title: DarGlobal Assistant
emoji: 🏢
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# DarGlobal & Wasalt assistant

A grounded chatbot over public DarGlobal and Wasalt data. FastAPI backend (`backend/`) serving a statically exported Next.js UI (`frontend/`) from one container on port 7860.

Run locally: from `backend/`, `uvicorn src.dar.main:app --reload --port 8000` (after `npm run build` in `frontend/`).
Deploy: Hugging Face Spaces (Docker). Set `OPENROUTER_API_KEY` (and optionally `OPENROUTER_API_KEY_2`) as Space secrets.
