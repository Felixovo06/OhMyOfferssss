from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.db.models import User
from app.schemas.common import ApiResponse
from app.schemas.groups import (
    AcceptInvitationResponse,
    CreateGroupRequest,
    CreateInvitationRequest,
    GroupInvitationOut,
    GroupMemberOut,
    GroupOut,
)
from app.services.groups.service import GroupService

router = APIRouter()


@router.get("/groups", response_model=ApiResponse[list[GroupOut]])
def list_groups(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[list[GroupOut]]:
    groups = GroupService(db).list_groups(current_user)
    return ApiResponse(data=[GroupOut.model_validate(group) for group in groups])


@router.post("/groups", response_model=ApiResponse[GroupOut])
def create_group(
    payload: CreateGroupRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[GroupOut]:
    group = GroupService(db).create_group(current_user, payload)
    return ApiResponse(data=GroupOut.model_validate(group))


@router.get("/groups/{group_id}", response_model=ApiResponse[GroupOut])
def get_group(
    group_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[GroupOut]:
    group = GroupService(db).get_group_for_member(current_user, group_id)
    return ApiResponse(data=GroupOut.model_validate(group))


@router.get("/groups/{group_id}/members", response_model=ApiResponse[list[GroupMemberOut]])
def list_members(
    group_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[list[GroupMemberOut]]:
    members = GroupService(db).list_members(current_user, group_id)
    return ApiResponse(data=[GroupMemberOut.model_validate(member) for member in members])


@router.post("/groups/{group_id}/invitations", response_model=ApiResponse[GroupInvitationOut])
def create_invitation(
    group_id: str,
    payload: CreateInvitationRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[GroupInvitationOut]:
    invitation = GroupService(db).create_invitation(current_user, group_id, payload)
    return ApiResponse(data=GroupInvitationOut.model_validate(invitation))


@router.get("/invitations/{token}", response_model=ApiResponse[GroupInvitationOut])
def get_invitation(
    token: str,
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[GroupInvitationOut]:
    invitation = GroupService(db).get_invitation(token)
    return ApiResponse(data=GroupInvitationOut.model_validate(invitation))


@router.post("/invitations/{token}/accept", response_model=ApiResponse[AcceptInvitationResponse])
def accept_invitation(
    token: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[AcceptInvitationResponse]:
    group = GroupService(db).accept_invitation(current_user, token)
    return ApiResponse(data=AcceptInvitationResponse(group=GroupOut.model_validate(group)))
