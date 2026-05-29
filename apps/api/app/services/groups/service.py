from datetime import UTC, datetime
from secrets import token_urlsafe

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.db.models import Group, GroupInvitation, GroupMember, User
from app.db.repositories.groups import GroupRepository
from app.schemas.groups import CreateGroupRequest, CreateInvitationRequest


class GroupService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.groups = GroupRepository(db)

    def list_groups(self, user: User) -> list[Group]:
        return self.groups.list_for_user(user.id)

    def create_group(self, user: User, payload: CreateGroupRequest) -> Group:
        group = self.groups.create(user, payload.name, payload.description)
        self.db.commit()
        self.db.refresh(group)
        return group

    def get_group_for_member(self, user: User, group_id: str) -> Group:
        self._require_member(user, group_id)
        group = self.groups.get(group_id)
        if group is None:
            raise AppError("GROUP_NOT_FOUND", "小组不存在", status_code=404)
        return group

    def list_members(self, user: User, group_id: str) -> list[GroupMember]:
        self._require_member(user, group_id)
        return self.groups.list_members(group_id)

    def create_invitation(
        self,
        user: User,
        group_id: str,
        payload: CreateInvitationRequest,
    ) -> GroupInvitation:
        self._require_owner(user, group_id)
        token = token_urlsafe(32)
        invitation = self.groups.create_invitation(group_id, user.id, token, payload.email)
        self.db.commit()
        self.db.refresh(invitation)
        return invitation

    def get_invitation(self, token: str) -> GroupInvitation:
        invitation = self.groups.get_invitation_by_token(token)
        if invitation is None:
            raise AppError("INVITATION_NOT_FOUND", "邀请不存在", status_code=404)
        return invitation

    def accept_invitation(self, user: User, token: str) -> Group:
        invitation = self.get_invitation(token)
        if invitation.status != "pending":
            raise AppError("INVITATION_USED", "邀请已被使用", status_code=409)
        if invitation.email and invitation.email.lower() != user.email.lower():
            raise AppError("INVITATION_EMAIL_MISMATCH", "当前账号无法接受该邀请", status_code=403)

        self.groups.add_member(invitation.group_id, user.id, "member")
        invitation.status = "accepted"
        invitation.accepted_by_id = user.id
        invitation.accepted_at = datetime.now(UTC)
        self.db.commit()

        group = self.groups.get(invitation.group_id)
        if group is None:
            raise AppError("GROUP_NOT_FOUND", "小组不存在", status_code=404)
        return group

    def _require_member(self, user: User, group_id: str) -> GroupMember:
        group = self.groups.get(group_id)
        if group is None:
            raise AppError("GROUP_NOT_FOUND", "小组不存在", status_code=404)
        member = self.groups.get_member(group_id, user.id)
        if member is None:
            raise AppError("FORBIDDEN", "无权访问该小组", status_code=403)
        return member

    def _require_owner(self, user: User, group_id: str) -> GroupMember:
        member = self._require_member(user, group_id)
        if member.role != "owner":
            raise AppError("FORBIDDEN", "只有小组 owner 可以执行该操作", status_code=403)
        return member

