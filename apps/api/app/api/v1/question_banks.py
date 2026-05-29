from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.db.models import User
from app.schemas.common import ApiResponse
from app.schemas.question_banks import QuestionBankCreate, QuestionBankOut, QuestionBankUpdate
from app.schemas.questions import QuestionCreate, QuestionOut
from app.services.question_banks.service import QuestionBankService
from app.services.questions.service import QuestionService

router = APIRouter()


@router.get("/question-banks", response_model=ApiResponse[list[QuestionBankOut]])
@router.get("/banks", response_model=ApiResponse[list[QuestionBankOut]])
def list_question_banks(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[list[QuestionBankOut]]:
    banks = QuestionBankService(db).list_banks(current_user)
    return ApiResponse(data=[bank_to_out(bank) for bank in banks])


@router.post("/question-banks", response_model=ApiResponse[QuestionBankOut])
@router.post("/banks", response_model=ApiResponse[QuestionBankOut])
def create_question_bank(
    payload: QuestionBankCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[QuestionBankOut]:
    bank = QuestionBankService(db).create_bank(current_user, payload)
    return ApiResponse(data=bank_to_out(bank))


@router.get("/question-banks/{bank_id}", response_model=ApiResponse[QuestionBankOut])
@router.get("/banks/{bank_id}", response_model=ApiResponse[QuestionBankOut])
def get_question_bank(
    bank_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[QuestionBankOut]:
    bank = QuestionBankService(db).get_accessible_bank(current_user, bank_id)
    return ApiResponse(data=bank_to_out(bank))


@router.patch("/question-banks/{bank_id}", response_model=ApiResponse[QuestionBankOut])
@router.patch("/banks/{bank_id}", response_model=ApiResponse[QuestionBankOut])
def update_question_bank(
    bank_id: str,
    payload: QuestionBankUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[QuestionBankOut]:
    bank = QuestionBankService(db).update_bank(current_user, bank_id, payload)
    return ApiResponse(data=bank_to_out(bank))


@router.delete("/question-banks/{bank_id}", response_model=ApiResponse[dict[str, bool]])
@router.delete("/banks/{bank_id}", response_model=ApiResponse[dict[str, bool]])
def delete_question_bank(
    bank_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[dict[str, bool]]:
    QuestionBankService(db).delete_bank(current_user, bank_id)
    return ApiResponse(data={"deleted": True})


@router.get("/question-banks/{bank_id}/questions", response_model=ApiResponse[list[QuestionOut]])
@router.get("/banks/{bank_id}/questions", response_model=ApiResponse[list[QuestionOut]])
def list_bank_questions(
    bank_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    tag: str | None = None,
    difficulty_label: str | None = None,
    enabled: bool | None = None,
    keyword: str | None = None,
    difficulty: str | None = None,
    status: str | None = None,
) -> ApiResponse[list[QuestionOut]]:
    difficulty_score = int(difficulty) if difficulty and difficulty.isdigit() else None
    if difficulty and difficulty_score is None and not difficulty_label:
        difficulty_label = difficulty
    if status and enabled is None:
        enabled = {"active": True, "enabled": True, "disabled": False}.get(status)
    questions = QuestionService(db).list_questions(
        current_user,
        bank_id,
        tag=tag,
        difficulty_score=difficulty_score,
        difficulty_label=difficulty_label,
        enabled=enabled,
        keyword=keyword,
    )
    return ApiResponse(data=[question_to_out(question) for question in questions])


@router.post("/question-banks/{bank_id}/questions", response_model=ApiResponse[QuestionOut])
@router.post("/banks/{bank_id}/questions", response_model=ApiResponse[QuestionOut])
def create_bank_question(
    bank_id: str,
    payload: QuestionCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[QuestionOut]:
    question = QuestionService(db).create_question(current_user, bank_id, payload)
    return ApiResponse(data=question_to_out(question))


def question_to_out(question) -> QuestionOut:  # type: ignore[no-untyped-def]
    return QuestionOut.model_validate(
        {
            **question.__dict__,
            "tags": question.tag_names,
            "content": question.question,
            "difficulty": question.difficulty_score,
            "status": "active" if question.enabled else "disabled",
        },
    )


def bank_to_out(bank) -> QuestionBankOut:  # type: ignore[no-untyped-def]
    return QuestionBankOut.model_validate(
        {
            **bank.__dict__,
            "owner_id": bank.created_by_id,
            "tags": bank.default_tags,
            "scope": "group" if bank.group_id else "personal",
            "question_count": len(getattr(bank, "questions", [])),
        },
    )
