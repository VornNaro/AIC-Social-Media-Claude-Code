import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.post import AuthorMini


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=1000)


class CommentOut(BaseModel):
    id: uuid.UUID
    post_id: uuid.UUID
    author: AuthorMini
    content: str
    created_at: datetime
