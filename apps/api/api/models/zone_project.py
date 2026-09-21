from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.db import Base
from api.models.base import TimestampMixin, UUIDPKMixin


class Zone(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "zones"

    name: Mapped[str] = mapped_column(String(150), unique=True)
    code: Mapped[str] = mapped_column(String(30), unique=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    user_access: Mapped[list["UserZoneAccess"]] = relationship(
        back_populates="zone", cascade="all, delete-orphan"
    )


class Project(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(150), unique=True)
    code: Mapped[str] = mapped_column(String(30), unique=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    user_access: Mapped[list["UserProjectAccess"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
