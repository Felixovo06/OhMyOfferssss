from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.users import UserOut


class CreateGroupRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class CreateInvitationRequest(BaseModel):
    email: EmailStr | None = None


class GroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    created_by_id: str
    owner_id: str
    member_count: int
    created_at: datetime
    updated_at: datetime


class GroupMemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    group_id: str
    user_id: str
    role: str
    user: UserOut
    joined_at: datetime
    created_at: datetime
    updated_at: datetime


class GroupInvitationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    group_id: str
    group_name: str
    email: str | None
    token: str
    invite_url: str
    status: str
    inviter_name: str
    expires_at: datetime | None
    created_by_id: str
    accepted_by_id: str | None
    accepted_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AcceptInvitationResponse(BaseModel):
    group: GroupOut
