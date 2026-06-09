import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.connection import ConnectionStatus


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
