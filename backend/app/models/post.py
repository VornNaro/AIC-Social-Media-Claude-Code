import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, uuid_pk


class Post(Base, TimestampMixin):
    __tablename__ = "posts"

    id: Mapped[uuid.UUID] = uuid_pk()
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    author: Mapped["User"] = relationship(back_populates="posts", lazy="noload")
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="post", cascade="all, delete-orphan", lazy="noload"
    )
    reactions: Mapped[list["Reaction"]] = relationship(
        back_populates="post", cascade="all, delete-orphan", lazy="noload"
    )
    shares: Mapped[list["Share"]] = relationship(
        back_populates="post", cascade="all, delete-orphan", lazy="noload"
    )

    __table_args__ = (
        CheckConstraint(
            "content IS NOT NULL OR image_url IS NOT NULL", name="content_or_image"
        ),
        # Composite indexes; Postgres scans them backward for ORDER BY ... DESC.
        Index("ix_posts_author_created", "author_id", "created_at"),
        Index("ix_posts_created", "created_at", "id"),
    )
