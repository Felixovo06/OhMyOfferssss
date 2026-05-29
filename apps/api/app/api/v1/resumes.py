from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.db.models import Resume, User
from app.schemas.common import ApiResponse
from app.schemas.resumes import ResumeOut, ResumeSummary
from app.services.resumes.service import ResumeService

router = APIRouter()


@router.get("/resumes", response_model=ApiResponse[list[ResumeOut]])
def list_resumes(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[list[ResumeOut]]:
    resumes = ResumeService(db).list_resumes(current_user)
    return ApiResponse(data=[resume_to_out(resume) for resume in resumes])


@router.post("/resumes", response_model=ApiResponse[ResumeOut])
async def upload_resume(
    file: Annotated[UploadFile, File()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[ResumeOut]:
    resume = await ResumeService(db).upload_resume(current_user, file)
    return ApiResponse(data=resume_to_out(resume))


@router.get("/resumes/{resume_id}", response_model=ApiResponse[ResumeOut])
def get_resume(
    resume_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[ResumeOut]:
    resume = ResumeService(db).get_resume(current_user, resume_id)
    return ApiResponse(data=resume_to_out(resume))


@router.delete("/resumes/{resume_id}", response_model=ApiResponse[dict[str, bool]])
def delete_resume(
    resume_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[dict[str, bool]]:
    ResumeService(db).delete_resume(current_user, resume_id)
    return ApiResponse(data={"deleted": True})


def resume_to_out(resume: Resume) -> ResumeOut:
    return ResumeOut.model_validate(
        {
            **resume.__dict__,
            "summary": (
                ResumeSummary.model_validate(resume.summary_json)
                if resume.summary_json
                else None
            ),
        },
    )
