# syntax=docker/dockerfile:1
# One image, one port: FastAPI serves the API and the statically exported Next.js UI.
# Built for Hugging Face Spaces (Docker SDK): port 7860, runs as user 1000.

# ---- 1. build the UI to static files -------------------------------------------------
FROM node:22-slim AS ui
WORKDIR /ui
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build            # next.config: output "export" -> /ui/out

# ---- 2. runtime ------------------------------------------------------------------------
FROM python:3.11-slim
RUN useradd -m -u 1000 user
ENV HOME=/home/user PATH=/home/user/.local/bin:$PATH PYTHONUNBUFFERED=1 PYTHONPATH=/app/backend/src
WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/src backend/src
COPY data/processed data/processed
COPY --from=ui /ui/out frontend/out
RUN chown -R user:user /app
USER user

# Build the vector index and download the embedding model NOW, so a cold start is a few seconds.
RUN python -m dar.main

EXPOSE 7860
# OPENROUTER_API_KEY is supplied at run time as a host secret. It is never baked into the image.
CMD ["python", "-m", "uvicorn", "dar.main:create_app_from_env", "--factory", "--host", "0.0.0.0", "--port", "7860"]
