from collections.abc import Generator
from typing import Annotated

from fastapi import Cookie, Depends, Header
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import decode_access_token
from app.db.models import User
from app.db.repositories.users import UserRepository
from app.db.session import SessionLocal

settings = get_settings()


def get_db() -> Generator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    authorization: Annotated[str | None, Header()] = None,
    cookie_token: Annotated[str | None, Cookie(alias=settings.auth_cookie_name)] = None,
) -> User:
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    elif cookie_token:
        token = cookie_token

    if not token:
        raise AppError("UNAUTHORIZED", "请先登录", status_code=401)

    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if not isinstance(user_id, str):
        raise AppError("UNAUTHORIZED", "登录状态无效，请重新登录", status_code=401)

    user = UserRepository(db).get(user_id)
    if user is None:
        raise AppError("UNAUTHORIZED", "用户不存在，请重新登录", status_code=401)
    return user
