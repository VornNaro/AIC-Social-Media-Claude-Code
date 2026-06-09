import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, uuid_pk


class RsvpStatus(str, enum.Enum):
    GOING = "GOING"
    MAYBE = "MAYBE"
    DECLINED = "DECLINED"


class Reunion(Base, TimestampMixin):
    """A reunion / event hosted within a school community."""

    __tablename__ = "reunions"

    id: Mapped[uuid.UUID] = uuid_pk()
    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), index=True, nullable=False
    )
    host_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    class_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    venue: Mapped[str | None] = mapped_column(String(160), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    cover_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    amenities: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, default=list, server_default="{}"
    )

    school: Mapped["School"] = relationship(back_populates="reunions", lazy="noload")
    host: Mapped["User"] = relationship(lazy="noload")
    rsvps: Mapped[list["Rsvp"]] = relationship(
        back_populates="reunion", cascade="all, delete-orphan", lazy="noload"
    )


class Rsvp(Base, TimestampMixin):
    """A user's RSVP to a reunion. One row per (user, reunion)."""

    __tablename__ = "rsvps"

    id: Mapped[uuid.UUID] = uuid_pk()
    reunion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reunions.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[RsvpStatus] = mapped_column(
        Enum(RsvpStatus, name="rsvp_status"), nullable=False
    )

    reunion: Mapped["Reunion"] = relationship(back_populates="rsvps", lazy="noload")
    user: Mapped["User"] = relationship(lazy="noload")

    __table_args__ = (
        UniqueConstraint("user_id", "reunion_id", name="uq_rsvps_user_reunion"),
    )
