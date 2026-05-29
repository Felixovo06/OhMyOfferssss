FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY apps/api/pyproject.toml apps/api/README.md apps/api/alembic.ini ./
COPY apps/api/app ./app
COPY apps/api/scripts ./scripts
COPY apps/api/docker-entrypoint.sh ./docker-entrypoint.sh

RUN pip install . \
    && chmod +x ./docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
