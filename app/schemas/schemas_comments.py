from pydantic import BaseModel
from datetime import datetime


class CommentCreate(BaseModel):
    content: str
    parent_id: int = None


class CommentOut(BaseModel):
    post_id: int
    parent_id: int | None
    id: int
    author_id: int
    is_blocked: bool
    block_reason: str | None
    created_at: datetime
    content: str

    class Config:
        orm_mode = True


class CommentUpdate(BaseModel):
    content: str
