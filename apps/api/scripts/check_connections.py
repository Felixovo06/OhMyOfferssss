from app.clients.database import ping_database
from app.clients.redis import ping_redis
from app.core.config import get_settings
from app.db.session import SessionLocal


def main() -> None:
    settings = get_settings()
    with SessionLocal() as db:
        ping_database(db)
    ping_redis()
    print(f"database=ok host={_host_hint(settings.database_url)}")
    print(f"redis=ok host={_host_hint(settings.redis_url)}")


def _host_hint(url: str) -> str:
    if "@" not in url:
        return url.split("://", 1)[-1].split("/", 1)[0]
    return url.rsplit("@", 1)[-1].split("/", 1)[0]


if __name__ == "__main__":
    main()
