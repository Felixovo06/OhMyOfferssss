from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, user_id: str) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email.lower())
        return self.db.scalars(statement).first()

    def create(self, email: str, password_hash: str, name: str | None) -> User:
        user = User(email=email.lower(), password_hash=password_hash, name=name)
        self.db.add(user)
        self.db.flush()
        return user

