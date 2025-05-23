from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel
import uuid

from app.models.base import BaseModel


class UserBase(SQLModel):
    email: str = Field(index=True, unique=True)
    username: str = Field(index=True, unique=True)
    is_active: bool = True
    is_superuser: bool = False


class User(UserBase, BaseModel, table=True):
    __tablename__ = "users"
    
    hashed_password: str


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: uuid.UUID


class UserUpdate(SQLModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None 