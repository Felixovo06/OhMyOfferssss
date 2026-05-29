# Ubuntu Docker Deployment

This guide deploys Ohmyoffer on a fresh Ubuntu server with Docker Compose.

## 1. Install Docker

```bash
sudo apt update
sudo apt install -y ca-certificates curl git
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker "$USER"
```

Log out and back in after `usermod`, or run the remaining commands with `sudo`.

## 2. Clone The App

```bash
git clone https://github.com/Felixovo06/OhMyOfferssss.git
cd OhMyOfferssss
git checkout codex/hybrid-interview-retrieval
```

## 3. Configure Secrets

```bash
cp .env.example .env
nano .env
```

At minimum, change:

```env
POSTGRES_PASSWORD=use-a-strong-password
JWT_SECRET=use-at-least-32-random-bytes
BACKEND_CORS_ORIGINS=http://YOUR_SERVER_IP
WEB_PORT=80
API_PORT=8000
```

Optional:

```env
LLM_API_KEY=...
LLM_BASE_URL=https://api.deepseek.com
FEISHU_APP_ID=...
FEISHU_APP_SECRET=...
```

The web container proxies browser requests from `/api/*` to the API container, so `NEXT_PUBLIC_API_BASE_URL` is not required for the default single-server deployment.

## 4. Start

```bash
docker compose up -d --build
```

The API container runs `alembic upgrade head` automatically before starting FastAPI.

Check status:

```bash
docker compose ps
docker compose logs -f api
docker compose logs -f web
```

Open:

```text
http://YOUR_SERVER_IP
```

## External PostgreSQL / Redis

If your PostgreSQL and Redis already live on another server, do not use the default compose file.
Fill these in `.env`:

```env
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@YOUR_DB_HOST:5432/postgres
REDIS_URL=redis://:YOUR_REDIS_PASSWORD@YOUR_REDIS_HOST:6379/0
```

Then start only the app containers:

```bash
docker compose -f docker-compose.external.yml up -d --build
```

The API container will run Alembic against the external PostgreSQL on startup.

API health checks:

```bash
curl http://YOUR_SERVER_IP/api/v1/auth/me
curl http://YOUR_SERVER_IP:8000/ready
```

The first command should return unauthorized before login; that still confirms the proxy reaches the API.

## 5. Update Deployment

```bash
git pull
docker compose up -d --build
```

## 6. Backup PostgreSQL

```bash
docker compose exec postgres sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' > ohmyoffer-backup.sql
```

Restore:

```bash
cat ohmyoffer-backup.sql | docker compose exec -T postgres sh -c 'psql -U "$POSTGRES_USER" "$POSTGRES_DB"'
```
