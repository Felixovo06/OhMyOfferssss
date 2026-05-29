# Ohmyoffer Web

Next.js frontend for the Ohmyoffer AI interview practice MVP.

## Local setup

```bash
cd apps/web
npm install
cp .env.example .env.local
npm run dev
```

Open `http://localhost:3000`.

## Environment variables

- `NEXT_PUBLIC_API_BASE_URL`: backend base URL, for example `http://127.0.0.1:8000`.
- `NEXT_PUBLIC_USE_MOCK`: optional. Set to `true` to use browser-side mock data without the backend.

Only `NEXT_PUBLIC_*` variables belong in this app. Backend secrets such as database URLs, Redis URLs, LLM API keys, JWT secrets, and Feishu secrets must stay in `apps/api/.env`.

## Verification

```bash
npm run lint
npm run build
```

The MVP expects the backend to be running before real API mode is used. In mock mode, the UI can be checked without backend services.
