# Project rules (read first)

- Goals: docs/GOALS.md. Spec: docs/PRD.md, docs/TECH_SPEC.md. Tickets: .scratch/dar-chatbot/issues/.
- **Binding rules:** docs/ENGINEERING_RULES.md. Strict Red -> Green -> Refactor; tests assert outcomes at module edges only; layered architecture enforced by backend/tests/test_architecture.py; PII is redacted with an in-memory vault and never stored.
- Run tests: `.venv\Scripts\python -m pytest` from `backend/`.
- Never commit secrets. Never bypass bot protection. Never scrape at runtime.
