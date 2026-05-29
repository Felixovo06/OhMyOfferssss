from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import get_settings
from app.core.security import create_access_token
from app.db.models import User
from app.schemas.auth import LoginRequest, LoginResponse
from app.schemas.common import ApiResponse
from app.schemas.users import UserOut
from app.services.auth.service import AuthService

router = APIRouter()


@router.post("/login", response_model=ApiResponse[LoginResponse])
def login(
    payload: LoginRequest,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[LoginResponse]:
    user = AuthService(db).login_or_register(payload.email, payload.password, payload.name)
    token = create_access_token(str(user.id))

    settings = get_settings()
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
    )
    return ApiResponse(
        data=LoginResponse(
            access_token=token,
            token=token,
            user=UserOut.model_validate(user),
        ),
    )


@router.post("/register", response_model=ApiResponse[LoginResponse])
def register(
    payload: LoginRequest,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[LoginResponse]:
    return login(payload, response, db)


@router.post("/logout", response_model=ApiResponse[dict[str, bool]])
def logout(response: Response) -> ApiResponse[dict[str, bool]]:
    settings = get_settings()
    response.delete_cookie(key=settings.auth_cookie_name)
    return ApiResponse(data={"logged_out": True})


@router.get("/me", response_model=ApiResponse[UserOut])
def me(current_user: Annotated[User, Depends(get_current_user)]) -> ApiResponse[UserOut]:
    return ApiResponse(data=UserOut.model_validate(current_user))
