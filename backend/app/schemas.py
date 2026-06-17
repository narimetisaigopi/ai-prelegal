from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class SigninRequest(BaseModel):
    email: EmailStr
    password: str


class AuthUser(BaseModel):
    id: int
    email: EmailStr


class DocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    doc_type: str = Field(min_length=1, max_length=100)
    content: dict[str, Any]


class DocumentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    doc_type: str | None = Field(default=None, min_length=1, max_length=100)
    content: dict[str, Any] | None = None


class DocumentResponse(BaseModel):
    id: int
    owner_id: int
    title: str
    doc_type: str
    content: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class ChatMessageRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation: list[dict[str, str]] = Field(default_factory=list)
    doc_type: str | None = None
    known_fields: dict[str, Any] = Field(default_factory=dict)


class ChatMessageResponse(BaseModel):
    reply: str
    extracted_fields: dict[str, Any]
    is_complete: bool
