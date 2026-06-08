import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


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


class UserProfile(UserPublic):
    """Public profile + aggregate counts."""

    post_count: int


class UserUpdate(BaseModel):
    """Partial profile update (only provided fields change)."""

    display_name: str | None = Field(default=None, min_length=1, max_length=80)
    bio: str | None = Field(default=None, max_length=500)
    avatar_url: str | None = Field(default=None, max_length=2000)
