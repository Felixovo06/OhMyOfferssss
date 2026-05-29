from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.v1.question_banks import question_to_out
from app.db.models import InterviewItem, InterviewSession, User
from app.schemas.common import ApiResponse
from app.schemas.interviews import (
    InterviewAnswerCreate,
    InterviewCreate,
    InterviewItemOut,
    InterviewQuestionFeedback,
    InterviewSessionOut,
    InterviewSummary,
)
from app.services.interviews.service import InterviewService

router = APIRouter()


@router.post("/interviews", response_model=ApiResponse[InterviewSessionOut])
def create_interview(
    payload: InterviewCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[InterviewSessionOut]:
    session = InterviewService(db).create_session(current_user, payload)
    return ApiResponse(data=session_to_out(session))


@router.get("/interviews", response_model=ApiResponse[list[InterviewSessionOut]])
def list_interviews(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[list[InterviewSessionOut]]:
    sessions = InterviewService(db).list_sessions(current_user)
    return ApiResponse(data=[session_to_out(session, include_items=False) for session in sessions])


@router.get("/interviews/{session_id}", response_model=ApiResponse[InterviewSessionOut])
def get_interview(
    session_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[InterviewSessionOut]:
    session = InterviewService(db).get_session(current_user, session_id)
    return ApiResponse(data=session_to_out(session))


@router.post(
    "/interviews/items/{item_id}/answer",
    response_model=ApiResponse[InterviewItemOut],
)
def answer_interview_item(
    item_id: str,
    payload: InterviewAnswerCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[InterviewItemOut]:
    item = InterviewService(db).answer_item(current_user, item_id, payload)
    return ApiResponse(data=item_to_out(item))


@router.post("/interviews/{session_id}/complete", response_model=ApiResponse[InterviewSessionOut])
def complete_interview(
    session_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[InterviewSessionOut]:
    session = InterviewService(db).complete_session(current_user, session_id)
    return ApiResponse(data=session_to_out(session))


def session_to_out(
    session: InterviewSession,
    *,
    include_items: bool = True,
) -> InterviewSessionOut:
    return InterviewSessionOut.model_validate(
        {
            **session.__dict__,
            "config": session.config_json,
            "summary": (
                InterviewSummary.model_validate(session.summary_json)
                if session.summary_json
                else None
            ),
            "items": [item_to_out(item) for item in session.items] if include_items else [],
        },
    )


def item_to_out(item: InterviewItem) -> InterviewItemOut:
    return InterviewItemOut.model_validate(
        {
            **item.__dict__,
            "feedback": (
                InterviewQuestionFeedback.model_validate(item.feedback_json)
                if item.feedback_json
                else None
            ),
            "question": question_to_out(item.question),
        },
    )

