from typing import Optional
from pydantic import BaseModel, EmailStr

from app.schemas.mixins import PasswordMixin


class UserCreate(BaseModel,PasswordMixin):
    email: EmailStr
    username: str
    password: str


class UserLogin(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    is_active: bool
    is_superuser: bool


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    sub: Optional[str] = None 