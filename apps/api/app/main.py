from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.clients.database import ping_database
from app.clients.redis import ping_redis
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.middleware import RequestIdMiddleware
from app.db.session import SessionLocal


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        openapi_url="/openapi.json",
        docs_url="/docs",
    )

    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ready", tags=["system"])
    def ready() -> dict[str, str]:
        with SessionLocal() as db:
            ping_database(db)
        ping_redis()
        return {"status": "ready"}

    return app


app = create_app()
