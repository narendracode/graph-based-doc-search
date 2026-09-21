import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.db import Base
from api.models.base import TimestampMixin, UUIDPKMixin


class UserRole(str, enum.Enum):
    super_admin = "super_admin"
    user = "user"


class User(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"), default=UserRole.user
    )
    is_active: Mapped[bool] = mapped_column(default=True)

    zone_access: Mapped[list["UserZoneAccess"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    project_access: Mapped[list["UserProjectAccess"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    zones = association_proxy("zone_access", "zone")
    projects = association_proxy("project_access", "project")


class UserZoneAccess(Base):
    __tablename__ = "user_zone_access"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    zone_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("zones.id", ondelete="CASCADE"), primary_key=True
    )

    user: Mapped["User"] = relationship(back_populates="zone_access")
    zone: Mapped["Zone"] = relationship(back_populates="user_access")


class UserProjectAccess(Base):
    __tablename__ = "user_project_access"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )

    user: Mapped["User"] = relationship(back_populates="project_access")
    project: Mapped["Project"] = relationship(back_populates="user_access")
