from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from app.models.connection import ConnectionStatus

if TYPE_CHECKING:
    from app.models.user import User


class ConnectionRequest(BaseModel):
    """Send a connection request to another user (by id)."""

    user_id: uuid.UUID


class ConnectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: ConnectionStatus
    requester_id: uuid.UUID
    addressee_id: uuid.UUID
    created_at: datetime


class ClassmateOut(BaseModel):
    """A directory/suggestion entry: a user plus my connection state with them."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    display_name: str
    avatar_url: str | None = None
    graduation_year: int | None = None
    city: str | None = None
    role: str | None = None
    # one of: none | pending_outgoing | pending_incoming | connected (relative to me)
    connection_state: str = "none"
    mutual_count: int = 0

    @classmethod
    def from_user(
        cls, user: User, *, connection_state: str = "none", mutual_count: int = 0
    ) -> ClassmateOut:
        """Build from a User ORM row, layering on my connection state with them."""
        return cls.model_validate(user).model_copy(
            update={"connection_state": connection_state, "mutual_count": mutual_count}
        )
