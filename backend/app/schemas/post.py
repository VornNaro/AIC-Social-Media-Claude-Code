import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AuthorMini(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    display_name: str
    avatar_url: str | None = None


class SharedBy(BaseModel):
    username: str
    display_name: str
    shared_at: datetime


class PostCreate(BaseModel):
    content: str | None = Field(default=None, max_length=5000)
    image_url: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def require_content_or_image(self) -> "PostCreate":
        if not (self.content and self.content.strip()) and not self.image_url:
            raise ValueError("A post must have content or an image_url.")
        return self


class PostUpdate(BaseModel):
    content: str | None = Field(default=None, max_length=5000)
    image_url: str | None = Field(default=None, max_length=2000)


class PostOut(BaseModel):
    id: uuid.UUID
    author: AuthorMini
    content: str | None
    image_url: str | None
    created_at: datetime
    updated_at: datetime
    reaction_counts: dict[str, int]
    my_reaction: str | None = None
    comment_count: int
    share_count: int
    shared_by_me: bool = False
    shared_by: SharedBy | None = None
