import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserOut(BaseModel):
    """The authenticated user's own profile (includes email)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    display_name: str
    email: EmailStr
    bio: str | None = None
    avatar_url: str | None = None
    created_at: datetime


class UserPublic(BaseModel):
    """Public profile view (no email)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    display_name: str
    bio: str | None = None
    avatar_url: str | None = None
    created_at: datetime
