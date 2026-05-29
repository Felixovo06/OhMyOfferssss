from fastapi import APIRouter

from app.api.v1 import auth, groups, imports, interviews, question_banks, questions

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(groups.router, tags=["groups"])
api_router.include_router(question_banks.router, tags=["question-banks"])
api_router.include_router(questions.router, tags=["questions"])
api_router.include_router(imports.router, tags=["imports"])
api_router.include_router(interviews.router, tags=["interviews"])
