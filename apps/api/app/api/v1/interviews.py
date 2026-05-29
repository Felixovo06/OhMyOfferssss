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
    InterviewDifficultyUpdate,
    InterviewItemOut,
    InterviewPlanOut,
    InterviewPlanRequest,
    InterviewQuestionFeedback,
    InterviewSessionOut,
    InterviewSummary,
)
from app.services.interviews.service import InterviewService

router = APIRouter()


@router.post("/interviews/plan", response_model=ApiResponse[InterviewPlanOut])
def plan_interview(
    payload: InterviewPlanRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[InterviewPlanOut]:
    plan = InterviewService(db).plan_interview(current_user, payload)
    return ApiResponse(data=plan)


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


@router.get("/interviews/{session_id}/summary", response_model=ApiResponse[InterviewSummary])
def get_interview_summary(
    session_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[InterviewSummary]:
    session = InterviewService(db).get_session(current_user, session_id)
    return ApiResponse(data=summary_to_out(session))


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


@router.patch(
    "/interviews/items/{item_id}/difficulty",
    response_model=ApiResponse[InterviewItemOut],
)
def update_interview_item_difficulty(
    item_id: str,
    payload: InterviewDifficultyUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[InterviewItemOut]:
    item = InterviewService(db).update_item_difficulty(current_user, item_id, payload)
    return ApiResponse(data=item_to_out(item))


@router.post("/interviews/{session_id}/complete", response_model=ApiResponse[InterviewSessionOut])
def complete_interview(
    session_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[InterviewSessionOut]:
    session = InterviewService(db).complete_session(current_user, session_id)
    return ApiResponse(data=session_to_out(session))


@router.post("/interviews/{session_id}/start", response_model=ApiResponse[InterviewSessionOut])
def start_interview(
    session_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[InterviewSessionOut]:
    session = InterviewService(db).start_session(current_user, session_id)
    return ApiResponse(data=session_to_out(session))


@router.post("/interviews/{session_id}/next", response_model=ApiResponse[InterviewSessionOut])
def next_interview_question(
    session_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    prefetch: bool = False,
) -> ApiResponse[InterviewSessionOut]:
    session = InterviewService(db).next_question(current_user, session_id, prefetch=prefetch)
    return ApiResponse(data=session_to_out(session))


def session_to_out(
    session: InterviewSession,
    *,
    include_items: bool = True,
) -> InterviewSessionOut:
    config = session.config_json or {}
    return InterviewSessionOut.model_validate(
        {
            **session.__dict__,
            "config": config,
            "flow_mode": external_flow_mode(str(config.get("flow_mode", "knowledge_first"))),
            "current_stage": current_stage(session),
            "stage_plan": config.get("stage_plan", []),
            "summary": summary_to_out(session) if session.summary_json else None,
            "items": [item_to_out(item) for item in session.items] if include_items else [],
        },
    )


def item_to_out(item: InterviewItem) -> InterviewItemOut:
    return InterviewItemOut.model_validate(
        {
            **item.__dict__,
            "stage": stage_label(item.stage),
            "intention": item.intent,
            "related_skills": [item.related_skill] if item.related_skill else [],
            "feedback": (
                InterviewQuestionFeedback.model_validate(item.feedback_json)
                if item.feedback_json
                else None
            ),
            "question": question_to_out(item.question),
        },
    )


def summary_to_out(session: InterviewSession) -> InterviewSummary:
    summary_json = session.summary_json or {
        "score": 0,
        "strengths": [],
        "weaknesses": [],
        "next_steps": [],
        "comment": "面试尚未生成总结。",
    }
    next_steps = list(summary_json.get("next_steps") or [])
    return InterviewSummary.model_validate(
        {
            **summary_json,
            "project_performance": summary_json.get("project_performance")
            or project_performance(session),
            "knowledge_performance": summary_json.get("knowledge_performance")
            or knowledge_performance(session),
            "review_plan": summary_json.get("review_plan")
            or [{"topic": step, "suggestion": step} for step in next_steps],
        },
    )


def current_stage(session: InterviewSession) -> str:
    if not session.items:
        return "准备第一题"
    for item in session.items:
        if item.status != "answered":
            return stage_label(item.stage)
    return "completed" if session.status == "completed" else "summary"


def external_flow_mode(flow_mode: str) -> str:
    if flow_mode == "project_first":
        return "project"
    if flow_mode == "knowledge_first":
        return "knowledge"
    return flow_mode


def stage_label(stage: str) -> str:
    labels = {
        "project_deep_dive": "项目追问",
        "project_follow_up": "项目追问",
        "knowledge_linked": "知识点考察",
        "knowledge_probe": "知识点考察",
        "knowledge": "知识点考察",
        "general_probe": "岗位通用",
    }
    return labels.get(stage, stage)


def project_performance(session: InterviewSession) -> list[dict[str, object]]:
    project_items = [item for item in session.items if item.related_project]
    if not project_items:
        return []
    scores = [
        int((item.feedback_json or {}).get("score", 0))
        for item in project_items
        if item.feedback_json
    ]
    return [
        {
            "project_name": project_items[0].related_project or "简历项目",
            "score": int(sum(scores) / len(scores)) if scores else 0,
            "comment": "根据项目相关追问的回答质量汇总。",
        },
    ]


def knowledge_performance(session: InterviewSession) -> list[dict[str, object]]:
    totals: dict[str, list[int]] = {}
    for item in session.items:
        if not item.feedback_json:
            continue
        score = int(item.feedback_json.get("score", 0))
        for tag in item.question.tag_names:
            totals.setdefault(tag, []).append(score)
    return [
        {"tag": tag, "mastery": round(sum(scores) / len(scores) / 100, 2)}
        for tag, scores in sorted(totals.items())
        if scores
    ]
