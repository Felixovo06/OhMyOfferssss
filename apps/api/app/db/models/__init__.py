import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def new_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    memberships: Mapped[list["GroupMember"]] = relationship(back_populates="user")


class Group(Base, TimestampMixin):
    __tablename__ = "groups"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    created_by_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)

    members: Mapped[list["GroupMember"]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
    )
    invitations: Mapped[list["GroupInvitation"]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
    )

    @property
    def owner_id(self) -> str:
        return self.created_by_id

    @property
    def member_count(self) -> int:
        return len(self.members)


class GroupMember(Base, TimestampMixin):
    __tablename__ = "group_members"
    __table_args__ = (UniqueConstraint("group_id", "user_id", name="uq_group_members_group_user"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    group_id: Mapped[str] = mapped_column(ForeignKey("groups.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="member")

    group: Mapped[Group] = relationship(back_populates="members")
    user: Mapped[User] = relationship(back_populates="memberships")

    @property
    def joined_at(self) -> datetime:
        return self.created_at


class GroupInvitation(Base, TimestampMixin):
    __tablename__ = "group_invitations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    group_id: Mapped[str] = mapped_column(ForeignKey("groups.id"), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    token: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    created_by_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    accepted_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    group: Mapped[Group] = relationship(back_populates="invitations")

    @property
    def invite_url(self) -> str:
        return f"/invite/{self.token}"

    @property
    def group_name(self) -> str:
        return self.group.name if self.group else ""

    @property
    def inviter_name(self) -> str:
        return ""

    @property
    def expires_at(self) -> datetime | None:
        return None


class QuestionBank(Base, TimestampMixin):
    __tablename__ = "question_banks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    group_id: Mapped[str | None] = mapped_column(ForeignKey("groups.id"), index=True)
    created_by_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    default_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    target_roles: Mapped[list[str]] = mapped_column(JSON, default=list)
    skill_keywords: Mapped[list[str]] = mapped_column(JSON, default=list)
    domains: Mapped[list[str]] = mapped_column(JSON, default=list)
    semantic_profile_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    questions: Mapped[list["Question"]] = relationship(
        back_populates="bank",
        cascade="all, delete-orphan",
    )

    @property
    def scope(self) -> str:
        return "group" if self.group_id else "personal"

    @property
    def question_count(self) -> int:
        return len(self.questions)


class FeishuSource(Base, TimestampMixin):
    __tablename__ = "feishu_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    document_id: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    document_type: Mapped[str] = mapped_column(String(50), nullable=False, default="docx")
    title: Mapped[str | None] = mapped_column(String(300))
    last_imported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sync_status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")


class Question(Base, TimestampMixin):
    __tablename__ = "questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    bank_id: Mapped[str] = mapped_column(
        ForeignKey("question_banks.id"),
        index=True,
        nullable=False,
    )
    source_id: Mapped[str | None] = mapped_column(ForeignKey("feishu_sources.id"), index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str | None] = mapped_column(Text)
    difficulty_score: Mapped[int | None] = mapped_column(Integer)
    difficulty_label: Mapped[str | None] = mapped_column(String(20))
    source_type: Mapped[str] = mapped_column(String(30), nullable=False, default="manual")
    source_block_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    bank: Mapped[QuestionBank] = relationship(back_populates="questions")
    tags: Mapped[list["QuestionTag"]] = relationship(
        back_populates="question",
        cascade="all, delete-orphan",
    )

    @property
    def tag_names(self) -> list[str]:
        return [question_tag.tag.name for question_tag in self.tags]


class Tag(Base, TimestampMixin):
    __tablename__ = "tags"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)

    questions: Mapped[list["QuestionTag"]] = relationship(
        back_populates="tag",
        cascade="all, delete-orphan",
    )


class QuestionTag(Base):
    __tablename__ = "question_tags"
    __table_args__ = (UniqueConstraint("question_id", "tag_id", name="uq_question_tags_pair"),)

    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"), primary_key=True)
    tag_id: Mapped[str] = mapped_column(ForeignKey("tags.id"), primary_key=True)

    question: Mapped[Question] = relationship(back_populates="tags")
    tag: Mapped[Tag] = relationship(back_populates="questions")


class ImportBatch(Base, TimestampMixin):
    __tablename__ = "import_batches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    bank_id: Mapped[str] = mapped_column(ForeignKey("question_banks.id"), nullable=False)
    source_id: Mapped[str] = mapped_column(ForeignKey("feishu_sources.id"), nullable=False)
    created_by_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    raw_blocks_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    normalized_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    ai_result_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    error_message: Mapped[str | None] = mapped_column(Text)

    source: Mapped[FeishuSource] = relationship()
    items: Mapped[list["ImportItem"]] = relationship(
        back_populates="batch",
        cascade="all, delete-orphan",
    )


class ImportItem(Base, TimestampMixin):
    __tablename__ = "import_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    batch_id: Mapped[str] = mapped_column(
        ForeignKey("import_batches.id"),
        index=True,
        nullable=False,
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    difficulty_score: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    difficulty_label: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    source_block_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    confidence: Mapped[int] = mapped_column(Integer, nullable=False, default=80)
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    confirmed_question_id: Mapped[str | None] = mapped_column(ForeignKey("questions.id"))

    batch: Mapped[ImportBatch] = relationship(back_populates="items")


class InterviewSession(Base, TimestampMixin):
    __tablename__ = "interview_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    created_by_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    resume_id: Mapped[str | None] = mapped_column(ForeignKey("resumes.id"), index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    mode: Mapped[str] = mapped_column(String(30), nullable=False, default="normal")
    target: Mapped[str | None] = mapped_column(String(300))
    config_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    strategy: Mapped[str] = mapped_column(Text, nullable=False, default="")
    selection_reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="ready")
    summary_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    items: Mapped[list["InterviewItem"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="InterviewItem.position",
    )
    resume: Mapped["Resume | None"] = relationship()


class InterviewItem(Base, TimestampMixin):
    __tablename__ = "interview_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("interview_sessions.id"),
        index=True,
        nullable=False,
    )
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"), index=True, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    selection_reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    stage: Mapped[str] = mapped_column(String(40), nullable=False, default="knowledge")
    intent: Mapped[str] = mapped_column(String(120), nullable=False, default="知识点考察")
    related_project: Mapped[str | None] = mapped_column(String(200))
    related_skill: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    answer: Mapped[str | None] = mapped_column(Text)
    feedback_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    session: Mapped[InterviewSession] = relationship(back_populates="items")
    question: Mapped[Question] = relationship()


class Resume(Base, TimestampMixin):
    __tablename__ = "resumes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    created_by_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(120))
    file_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="parsing")
    is_scanned: Mapped[bool | None] = mapped_column(Boolean)
    error_message: Mapped[str | None] = mapped_column(Text)
    summary_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
