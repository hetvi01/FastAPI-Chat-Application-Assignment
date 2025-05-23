from datetime import datetime, timezone
import uuid
from typing import Optional
from sqlmodel import Field, SQLModel
from sqlalchemy import DateTime


class UUIDModel(SQLModel):
    """Base model with UUID primary key"""
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )


class TimestampModel(SQLModel):
    """Base model with created_at and updated_at timestamps"""
    # Specify the timezone-aware datetime type in a way compatible with all SQLModel versions
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True)
    )


class BaseModel(UUIDModel, TimestampModel):
    """Base model with UUID primary key and timestamp fields"""
    pass