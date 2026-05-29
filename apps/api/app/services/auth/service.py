from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import hash_password, verify_password
from app.db.models import User
from app.db.repositories.users import UserRepository


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    def login_or_register(self, email: str, password: str, name: str | None) -> User:
        user = self.users.get_by_email(email)
        if user is None:
            user = self.users.create(email, hash_password(password), name)
            self.db.commit()
            self.db.refresh(user)
            return user

        if not verify_password(password, user.password_hash):
            raise AppError("INVALID_CREDENTIALS", "邮箱或密码错误", status_code=401)

        return user

