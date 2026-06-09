import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.reunion import RsvpStatus
from app.schemas.post import AuthorMini


class ReunionCreate(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    class_year: int | None = Field(default=None, ge=1900, le=2100)
    starts_at: datetime
    ends_at: datetime | None = None
    venue: str | None = Field(default=None, max_length=160)
    address: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=120)
    cover_url: str | None = Field(default=None, max_length=2000)
    description: str | None = Field(default=None, max_length=4000)
    amenities: list[str] = Field(default_factory=list, max_length=12)


class ReunionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    school_id: uuid.UUID
    title: str
    class_year: int | None = None
    starts_at: datetime
    ends_at: datetime | None = None
    venue: str | None = None
    address: str | None = None
    city: str | None = None
    cover_url: str | None = None
    description: str | None = None
    amenities: list[str] = []
    host: AuthorMini
    going_count: int = 0
    my_rsvp: RsvpStatus | None = None


class RsvpIn(BaseModel):
    status: RsvpStatus


class AttendeeOut(BaseModel):
    """A user who RSVP'd, plus their status."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    display_name: str
    avatar_url: str | None = None
    graduation_year: int | None = None
    city: str | None = None
    status: RsvpStatus
