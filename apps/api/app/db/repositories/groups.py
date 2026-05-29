from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import Group, GroupInvitation, GroupMember, User


class GroupRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_user(self, user_id: str) -> list[Group]:
        statement = (
            select(Group)
            .options(selectinload(Group.members))
            .join(GroupMember)
            .where(GroupMember.user_id == user_id)
            .order_by(Group.created_at.desc())
        )
        return list(self.db.scalars(statement).all())

    def get(self, group_id: str) -> Group | None:
        statement = select(Group).options(selectinload(Group.members)).where(Group.id == group_id)
        return self.db.scalars(statement).first()

    def get_with_members(self, group_id: str) -> Group | None:
        statement = (
            select(Group)
            .options(selectinload(Group.members).selectinload(GroupMember.user))
            .where(Group.id == group_id)
        )
        return self.db.scalars(statement).first()

    def create(self, user: User, name: str, description: str | None) -> Group:
        group = Group(name=name, description=description, created_by_id=user.id)
        self.db.add(group)
        self.db.flush()
        self.db.add(GroupMember(group_id=group.id, user_id=user.id, role="owner"))
        self.db.flush()
        return group

    def get_member(self, group_id: str, user_id: str) -> GroupMember | None:
        statement = select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id,
        )
        return self.db.scalars(statement).first()

    def add_member(self, group_id: str, user_id: str, role: str = "member") -> GroupMember:
        existing = self.get_member(group_id, user_id)
        if existing:
            return existing
        member = GroupMember(group_id=group_id, user_id=user_id, role=role)
        self.db.add(member)
        self.db.flush()
        return member

    def list_members(self, group_id: str) -> list[GroupMember]:
        statement = (
            select(GroupMember)
            .options(selectinload(GroupMember.user))
            .where(GroupMember.group_id == group_id)
            .order_by(GroupMember.created_at.asc())
        )
        return list(self.db.scalars(statement).all())

    def create_invitation(
        self,
        group_id: str,
        created_by_id: str,
        token: str,
        email: str | None,
    ) -> GroupInvitation:
        invitation = GroupInvitation(
            group_id=group_id,
            created_by_id=created_by_id,
            token=token,
            email=email,
        )
        self.db.add(invitation)
        self.db.flush()
        return invitation

    def get_invitation_by_token(self, token: str) -> GroupInvitation | None:
        statement = (
            select(GroupInvitation)
            .options(selectinload(GroupInvitation.group))
            .where(GroupInvitation.token == token)
        )
        return self.db.scalars(statement).first()
