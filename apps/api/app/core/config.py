from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Ohmyoffer API"
    environment: str = "local"
    api_v1_prefix: str = "/api/v1"
    backend_cors_origins_raw: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        alias="BACKEND_CORS_ORIGINS",
    )

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/ohmyoffer"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = "change-me-in-env"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7
    auth_cookie_name: str = "ohmyoffer_access_token"
    secure_cookies: bool = False

    llm_model: str = "deepseek-v4-flash"
    llm_thinking_enabled: bool = False
    llm_api_key: str | None = None
    llm_base_url: str | None = None

    feishu_app_id: str | None = None
    feishu_app_secret: str | None = None
    feishu_api_base_url: str = "https://open.feishu.cn/open-apis"
    feishu_token_cache_ttl_seconds: int = 6600

    github_proxy_url: str | None = "socks5h://127.0.0.1:10808"

    @property
    def backend_cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.backend_cors_origins_raw.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
