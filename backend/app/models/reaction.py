import enum
import uuid

from sqlalchemy import Enum, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAtMixin, uuid_pk


class ReactionType(str, enum.Enum):
    LIKE = "LIKE"
    LOVE = "LOVE"
    HAHA = "HAHA"
    WOW = "WOW"
    SAD = "SAD"
    ANGRY = "ANGRY"


class Reaction(Base, CreatedAtMixin):
    __tablename__ = "reactions"

    id: Mapped[uuid.UUID] = uuid_pk()
    post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[ReactionType] = mapped_column(
        Enum(ReactionType, name="reaction_type"), nullable=False
    )

    post: Mapped["Post"] = relationship(back_populates="reactions", lazy="noload")
    user: Mapped["User"] = relationship(back_populates="reactions", lazy="noload")

    # One reaction per user per post (also serves the toggle lookup).
    __table_args__ = (
        UniqueConstraint("user_id", "post_id", name="uq_reactions_user_post"),
    )
