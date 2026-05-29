from pydantic import BaseModel, EmailStr, Field

from app.schemas.users import UserOut


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    name: str | None = Field(default=None, max_length=100)


class LoginResponse(BaseModel):
    access_token: str
    token: str
    token_type: str = "bearer"
    user: UserOut
