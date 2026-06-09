import uuid

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAtMixin, TimestampMixin, uuid_pk


class School(Base, TimestampMixin):
    __tablename__ = "schools"

    id: Mapped[uuid.UUID] = uuid_pk()
    slug: Mapped[str] = mapped_column(String(60), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    short_name: Mapped[str | None] = mapped_column(String(20), nullable=True)
    location: Mapped[str | None] = mapped_column(String(160), nullable=True)
    founded: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cover_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    motto: Mapped[str | None] = mapped_column(String(160), nullable=True)

    memberships: Mapped[list["SchoolMembership"]] = relationship(
        back_populates="school", cascade="all, delete-orphan", lazy="noload"
    )
    reunions: Mapped[list["Reunion"]] = relationship(
        back_populates="school", cascade="all, delete-orphan", lazy="noload"
    )
    members: Mapped[list["User"]] = relationship(back_populates="school", lazy="noload")


class SchoolMembership(Base, CreatedAtMixin):
    """A user belonging to (having joined) a school community."""

    __tablename__ = "school_memberships"

    id: Mapped[uuid.UUID] = uuid_pk()
    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    school: Mapped["School"] = relationship(back_populates="memberships", lazy="noload")
    user: Mapped["User"] = relationship(back_populates="memberships", lazy="noload")

    __table_args__ = (
        UniqueConstraint("user_id", "school_id", name="uq_school_memberships_user_school"),
    )
