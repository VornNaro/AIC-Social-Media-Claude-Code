import enum
import uuid

from sqlalchemy import CheckConstraint, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, uuid_pk


class ConnectionStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"


class Connection(Base, TimestampMixin):
    """A classmate connection request/relationship between two users.

    Directed: requester_id sent the request to addressee_id. A single accepted
    row represents the (undirected) friendship.
    """

    __tablename__ = "connections"

    id: Mapped[uuid.UUID] = uuid_pk()
    requester_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    addressee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    status: Mapped[ConnectionStatus] = mapped_column(
        Enum(ConnectionStatus, name="connection_status"),
        nullable=False,
        default=ConnectionStatus.PENDING,
    )

    requester: Mapped["User"] = relationship(foreign_keys=[requester_id], lazy="noload")
    addressee: Mapped["User"] = relationship(foreign_keys=[addressee_id], lazy="noload")

    __table_args__ = (
        UniqueConstraint("requester_id", "addressee_id", name="uq_connections_requester_addressee"),
        CheckConstraint("requester_id <> addressee_id", name="no_self_connection"),
    )
