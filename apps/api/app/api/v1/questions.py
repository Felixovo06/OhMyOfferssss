from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.v1.question_banks import question_to_out
from app.db.models import User
from app.db.repositories.questions import QuestionRepository
from app.schemas.common import ApiResponse
from app.schemas.questions import QuestionOut, QuestionUpdate, TagOut
from app.services.questions.service import QuestionService

router = APIRouter()


@router.patch("/questions/{question_id}", response_model=ApiResponse[QuestionOut])
def update_question(
    question_id: str,
    payload: QuestionUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[QuestionOut]:
    question = QuestionService(db).update_question(current_user, question_id, payload)
    return ApiResponse(data=question_to_out(question))


@router.delete("/questions/{question_id}", response_model=ApiResponse[dict[str, bool]])
def delete_question(
    question_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[dict[str, bool]]:
    QuestionService(db).delete_question(current_user, question_id)
    return ApiResponse(data={"deleted": True})


@router.get("/tags", response_model=ApiResponse[list[TagOut]])
def list_tags(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[list[TagOut]]:
    _ = current_user
    tags = QuestionRepository(db).list_tags()
    return ApiResponse(data=[TagOut.model_validate(tag) for tag in tags])

