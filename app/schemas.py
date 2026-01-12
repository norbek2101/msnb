import re
from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    full_name: str
    password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if len(v) < 3 or len(v) > 32:
            raise ValueError("Username must be between 3 and 32 characters")
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Username can only contain letters, numbers, and underscores")
        return v

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        if len(v) < 2 or len(v) > 100:
            raise ValueError("Full name must be between 2 and 100 characters")
        if not re.match(r"^[\w\s\-]+$", v, re.UNICODE):
            raise ValueError("Full name can only contain letters, spaces, and hyphens")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class UserUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if len(v) < 3 or len(v) > 32:
            raise ValueError("Username must be between 3 and 32 characters")
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Username can only contain letters, numbers, and underscores")
        return v

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if len(v) < 2 or len(v) > 100:
            raise ValueError("Full name must be between 2 and 100 characters")
        if not re.match(r"^[\w\s\-]+$", v, re.UNICODE):
            raise ValueError("Full name can only contain letters, spaces, and hyphens")
        return v


class UserResponse(BaseModel):
    id: UUID
    email: str
    username: str
    full_name: str
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserProfile(BaseModel):
    id: UUID
    username: str
    full_name: str

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: str

    @field_validator("password")
    @classmethod
    def check_credentials(cls, v: str, info) -> str:
        return v


class PostCreate(BaseModel):
    title: str
    content: str

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        if len(v) < 5 or len(v) > 255:
            raise ValueError("Title must be between 5 and 255 characters")
        return v

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        if len(v) > 10000:
            raise ValueError("Content must not exceed 10000 characters")
        return v


class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if len(v) < 5 or len(v) > 255:
            raise ValueError("Title must be between 5 and 255 characters")
        return v

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if len(v) > 10000:
            raise ValueError("Content must not exceed 10000 characters")
        return v


class PostResponse(BaseModel):
    id: UUID
    author_id: UUID
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
    author: Optional[UserProfile] = None
    likes_count: int = 0
    comments_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class PostDetailResponse(PostResponse):
    comments: list["CommentResponse"] = []
    likes: list[UUID] = []


class CommentCreate(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        if len(v) > 2000:
            raise ValueError("Comment must not exceed 2000 characters")
        if len(v) < 1:
            raise ValueError("Comment cannot be empty")
        return v


class CommentResponse(BaseModel):
    id: UUID
    post_id: UUID
    author_id: UUID
    content: str
    created_at: datetime
    author: Optional[UserProfile] = None

    model_config = ConfigDict(from_attributes=True)


class LikeResponse(BaseModel):
    id: UUID
    user_id: UUID
    post_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FeedPostResponse(BaseModel):
    id: UUID
    title: str
    content: str
    likes: list[UUID] = []

    model_config = ConfigDict(from_attributes=True)


class FeedUserResponse(BaseModel):
    username: str
    posts: list[FeedPostResponse] = []

    model_config = ConfigDict(from_attributes=True)


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
    pages: int


class MessageResponse(BaseModel):
    message: str