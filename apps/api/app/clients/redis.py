from redis import Redis

from app.core.config import get_settings


def get_redis_client() -> Redis:
    return Redis.from_url(
        get_settings().redis_url,
        decode_responses=True,
        socket_connect_timeout=3,
        socket_timeout=3,
        protocol=2,
    )


def ping_redis() -> bool:
    return bool(get_redis_client().ping())
