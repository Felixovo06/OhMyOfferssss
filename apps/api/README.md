# Ohmyoffer API

FastAPI backend for the AI interview question bank app.

## Local setup

```bash
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
alembic upgrade head
fastapi dev app/main.py
```

OpenAPI is available at:

- `http://127.0.0.1:8000/openapi.json`
- `http://127.0.0.1:8000/docs`

## Stage 1 accounts

The first login for a new email creates that user automatically. Later logins require the same password.

