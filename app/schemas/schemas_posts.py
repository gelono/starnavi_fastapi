from pydantic import BaseModel


class PostBase(BaseModel):
    title: str
    content: str


class PostCreate(PostBase):
    auto_reply_enabled: bool = False
    reply_delay: int = 0


class PostOut(PostBase):
    id: int
    author_id: int
    auto_reply_enabled: bool
    reply_delay: int
    is_blocked: bool
    block_reason: str | None

    class Config:
        orm_mode = True


class PostUpdate(PostBase):
    title: str = None
    content: str = None
    auto_reply_enabled: bool = False
    reply_delay: int = 0
