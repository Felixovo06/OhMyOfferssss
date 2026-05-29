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

## Environment variables

Copy `.env.example` to `.env` for local development. Keep `.env` private; it is ignored by git.

- `APP_NAME`, `ENVIRONMENT`, `API_V1_PREFIX`: service name, runtime environment, and API prefix.
- `BACKEND_CORS_ORIGINS`: comma-separated frontend origins allowed by CORS.
- `DATABASE_URL`: PostgreSQL connection string. Use local credentials in development and secret-managed credentials in deployment.
- `REDIS_URL`: Redis connection string for cache and Feishu tenant token storage.
- `JWT_SECRET`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`: auth token signing and lifetime.
- `AUTH_COOKIE_NAME`, `SECURE_COOKIES`: browser cookie settings. Set `SECURE_COOKIES=true` behind HTTPS.
- `LLM_MODEL`, `LLM_THINKING_ENABLED`, `LLM_API_KEY`, `LLM_BASE_URL`: optional LLM provider settings. Without an API key/base URL the backend uses deterministic local fallbacks.
- `FEISHU_APP_ID`, `FEISHU_APP_SECRET`, `FEISHU_API_BASE_URL`, `FEISHU_TOKEN_CACHE_TTL_SECONDS`: Feishu app credentials and token cache settings.

## LLM setup

The backend calls an OpenAI-compatible `POST /chat/completions` endpoint when both `LLM_API_KEY` and `LLM_BASE_URL` are set. If either is missing, it keeps using deterministic local fallback logic so the MVP can still run offline.

Configure your private `.env`:

```bash
LLM_MODEL=deepseek-v4-flash
LLM_THINKING_ENABLED=false
LLM_API_KEY=...
LLM_BASE_URL=https://api.deepseek.com
```

The client asks for JSON object responses and validates the shape before writing extracted questions, interview selections, feedback, or summaries. It keeps thinking off for extraction/scoring and enables it for selection/summary, where deeper reasoning is more useful. Provider/network failures become `LLM_REQUEST_FAILED` or `LLM_INVALID_RESPONSE` API errors instead of leaking raw provider responses.

## Feishu app setup

Create an internal Feishu app in the Feishu/Lark developer console, then copy the app ID and app secret into your private `.env`.

Required capabilities for MVP import:

- Enable document read access for Docs/Wiki content.
- Add the document scopes needed to read blocks for the docs your users import.
- Install or publish the app to the tenant/workspace that owns the source documents.
- Make sure imported documents are shared with the app or with a user context the app can access.

The backend exchanges `FEISHU_APP_ID` and `FEISHU_APP_SECRET` for a tenant access token and caches it in Redis. Do not commit real app secrets or copied tenant tokens.

Supported import URLs:

- `https://*.feishu.cn/docx/<document_id>`
- `https://*.feishu.cn/doc/<document_id>`
- `https://*.feishu.cn/wiki/<wiki_token>` for wiki nodes that resolve to doc/docx content

## Integration checks

After filling `.env`, run:

```bash
python -m scripts.check_connections
python -m scripts.check_integrations --llm
python -m scripts.check_integrations --feishu-url "https://your.feishu.cn/docx/..."
```

The check scripts print only status, ids, host hints, and counts; they do not print API keys, app secrets, tenant tokens, or database passwords.

## Stage 5 operational checks

- Every response includes an `x-request-id` header; JSON API responses include the same `request_id` field.
- Handled errors use `{ success: false, error, request_id }` and unexpected errors are logged with the request ID.
- Generate the stable OpenAPI contract with:

```bash
python - <<'PY'
import json
from app.main import create_app

print(json.dumps(create_app().openapi(), ensure_ascii=False, indent=2))
PY
```
