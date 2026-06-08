import uuid

from sqlalchemy import ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAtMixin, uuid_pk


class Share(Base, CreatedAtMixin):
    __tablename__ = "shares"

    id: Mapped[uuid.UUID] = uuid_pk()
    post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    post: Mapped["Post"] = relationship(back_populates="shares", lazy="noload")
    user: Mapped["User"] = relationship(back_populates="shares", lazy="noload")

    # One repost per user per post → idempotent share.
    __table_args__ = (
        UniqueConstraint("user_id", "post_id", name="uq_shares_user_post"),
        # (created_at, id) so the feed's keyset tiebreak on event_id is index-backed.
        Index("ix_shares_created", "created_at", "id"),
    )
