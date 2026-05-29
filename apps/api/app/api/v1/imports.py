from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import get_settings
from app.db.models import User
from app.schemas.common import ApiResponse
from app.schemas.imports import (
    FeishuImportRequest,
    GithubImportRequest,
    ImportBatchOut,
    ImportConfirmResponse,
    ImportDetailOut,
    ImportItemOut,
    ImportItemUpdate,
    ImportRejectResponse,
)
from app.services.imports.service import (
    ImportService,
    process_confirm_import_batch,
    process_feishu_import_batch,
)

router = APIRouter()


@router.post("/imports/feishu", response_model=ApiResponse[ImportBatchOut])
@router.post("/imports", response_model=ApiResponse[ImportBatchOut])
def import_feishu(
    payload: FeishuImportRequest,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[ImportBatchOut]:
    service = ImportService(db)
    batch = service.queue_feishu_import(current_user, payload)
    if get_settings().environment == "test":
        service.process_queued_import_batch(batch.id)
        batch = service.get_batch_for_user(current_user, batch.id)
    else:
        background_tasks.add_task(process_feishu_import_batch, batch.id)
    return ApiResponse(data=batch_to_out(batch))


@router.post("/imports/github", response_model=ApiResponse[ImportBatchOut])
def import_github(
    payload: GithubImportRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[ImportBatchOut]:
    batch = ImportService(db).import_github_markdown(current_user, payload)
    return ApiResponse(data=batch_to_out(batch))


@router.get("/imports", response_model=ApiResponse[list[ImportBatchOut]])
def list_import_batches(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[list[ImportBatchOut]]:
    batches = ImportService(db).list_batches(current_user)
    return ApiResponse(data=[batch_to_out(batch) for batch in batches])


@router.get("/imports/{batch_id}", response_model=ApiResponse[ImportDetailOut])
def get_import_batch(
    batch_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[ImportDetailOut]:
    batch = ImportService(db).get_batch_for_user(current_user, batch_id)
    batch_out = batch_to_out(batch)
    return ApiResponse(data=ImportDetailOut(batch=batch_out, items=batch_out.items))


@router.get("/imports/{batch_id}/items", response_model=ApiResponse[list[ImportItemOut]])
def list_import_items(
    batch_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[list[ImportItemOut]]:
    items = ImportService(db).list_items(current_user, batch_id)
    return ApiResponse(data=[item_to_out(item) for item in items])


@router.patch("/import-items/{item_id}", response_model=ApiResponse[ImportItemOut])
def update_import_item(
    item_id: str,
    payload: ImportItemUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[ImportItemOut]:
    item = ImportService(db).update_item(current_user, item_id, payload)
    return ApiResponse(data=item_to_out(item))


@router.post("/imports/items/{item_id}/confirm", response_model=ApiResponse[ImportItemOut])
def confirm_import_item(
    item_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[ImportItemOut]:
    item, _ = ImportService(db).confirm_item(current_user, item_id)
    return ApiResponse(data=item_to_out(item))


@router.post("/imports/items/{item_id}/reject", response_model=ApiResponse[ImportItemOut])
def reject_import_item(
    item_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[ImportItemOut]:
    item = ImportService(db).reject_item(current_user, item_id)
    return ApiResponse(data=item_to_out(item))


@router.post("/imports/{batch_id}/reject", response_model=ApiResponse[ImportRejectResponse])
def reject_import_batch(
    batch_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[ImportRejectResponse]:
    count = ImportService(db).reject_batch(current_user, batch_id)
    return ApiResponse(data=ImportRejectResponse(rejected_count=count))


@router.post("/imports/{batch_id}/confirm", response_model=ApiResponse[ImportConfirmResponse])
def confirm_import_batch(
    batch_id: str,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[ImportConfirmResponse]:
    service = ImportService(db)
    count = service.queue_confirm_batch(current_user, batch_id)
    if count:
        if get_settings().environment == "test":
            count, question_ids = service.confirm_batch(current_user, batch_id)
            return ApiResponse(
                data=ImportConfirmResponse(confirmed_count=count, question_ids=question_ids),
            )
        else:
            background_tasks.add_task(process_confirm_import_batch, batch_id, current_user.id)
    return ApiResponse(
        data=ImportConfirmResponse(confirmed_count=0, question_ids=[]),
    )


def item_to_out(item) -> ImportItemOut:  # type: ignore[no-untyped-def]
    frontend_status = "rejected" if item.status == "discarded" else item.status
    frontend_confidence = item.confidence / 100 if item.confidence > 1 else item.confidence
    return ImportItemOut.model_validate(
        {
            **item.__dict__,
            "content": item.question,
            "question_content": item.question,
            "question_answer": item.answer,
            "status": frontend_status,
            "confidence": frontend_confidence,
            "difficulty": item.difficulty_score,
        },
    )


def batch_to_out(batch) -> ImportBatchOut:  # type: ignore[no-untyped-def]
    return ImportBatchOut.model_validate(
        {
            **batch.__dict__,
            "items": [item_to_out(item) for item in getattr(batch, "items", [])],
            "source_url": batch.source.url if getattr(batch, "source", None) else "",
            "status": _batch_status_for_frontend(batch),
            "total_count": len(getattr(batch, "items", [])),
            "confirmed_count": len(
                [item for item in getattr(batch, "items", []) if item.status == "confirmed"],
            ),
        },
    )


def _batch_status_for_frontend(batch) -> str:  # type: ignore[no-untyped-def]
    return batch.status
