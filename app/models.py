from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship, validates
import datetime
from passlib.context import CryptContext
from app.database.session import Base


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# User Model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    posts = relationship("Post", back_populates="author")  # Contact the Post model

    def verify_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.hashed_password)

    @classmethod
    def hash_password(cls, password: str) -> str:
        return pwd_context.hash(password)

# Post Model
class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Relationship with User model
    is_blocked = Column(Boolean, default=False)
    block_reason = Column(String(255), nullable=True, default="")
    auto_reply_enabled = Column(Boolean, default=False)
    reply_delay = Column(Integer, default=0)

    author = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post")

    @validates("title", "content")
    def validate_non_empty_string(self, key, value):
        if not value or value.strip() == "":
            raise ValueError(f"{key.capitalize()} cannot be an empty string.")
        return value

# Comment Model
class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"))
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)
    author_id = Column(Integer, ForeignKey("users.id"))
    is_blocked = Column(Boolean, default=False)
    block_reason = Column(String(255), nullable=True, default="")

    post = relationship("Post", back_populates="comments")
    replies = relationship("Comment", back_populates="parent", cascade="all, delete-orphan")
    parent = relationship("Comment", remote_side=id, back_populates="replies")

    @validates("content")
    def validate_non_empty_string(self, key, value):
        if not value or value.strip() == "":
            raise ValueError(f"{key.capitalize()} cannot be an empty string.")
        return value
