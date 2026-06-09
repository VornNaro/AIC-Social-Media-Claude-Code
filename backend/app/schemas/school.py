import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SchoolCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    short_name: str | None = Field(default=None, max_length=20)
    location: str | None = Field(default=None, max_length=160)
    founded: int | None = Field(default=None, ge=1000, le=2100)
    cover_url: str | None = Field(default=None, max_length=2000)
    motto: str | None = Field(default=None, max_length=160)


class SchoolOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    name: str
    short_name: str | None = None
    location: str | None = None
    founded: int | None = None
    cover_url: str | None = None
    motto: str | None = None
    member_count: int = 0
    is_member: bool = False
    created_at: datetime
