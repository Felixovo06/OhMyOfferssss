from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Resume


class ResumeRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_user(self, user_id: str) -> list[Resume]:
        statement = (
            select(Resume)
            .where(Resume.created_by_id == user_id)
            .order_by(Resume.updated_at.desc())
        )
        return list(self.db.scalars(statement).all())

    def get(self, resume_id: str) -> Resume | None:
        return self.db.get(Resume, resume_id)

    def create(
        self,
        *,
        user_id: str,
        filename: str,
        content_type: str | None,
        file_size: int,
    ) -> Resume:
        resume = Resume(
            created_by_id=user_id,
            filename=filename,
            content_type=content_type,
            file_size=file_size,
            status="parsing",
        )
        self.db.add(resume)
        self.db.flush()
        return resume

