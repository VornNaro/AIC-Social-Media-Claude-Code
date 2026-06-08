from pydantic import BaseModel

from app.models.reaction import ReactionType


class ReactionRequest(BaseModel):
    type: ReactionType


class ReactionState(BaseModel):
    my_reaction: ReactionType | None = None
    reaction_counts: dict[str, int]


class ShareState(BaseModel):
    share_count: int
    shared_by_me: bool
