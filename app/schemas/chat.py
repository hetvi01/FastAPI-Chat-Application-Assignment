from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID


class ChatType(str, Enum):
    PERSONAL = "personal"
    BRANCH = "branch"


class ChatCreate(BaseModel):
    name: str
    chat_type: ChatType = ChatType.PERSONAL


class ChatUpdate(BaseModel):
    name: Optional[str] = None
    active: Optional[bool] = None


class ChatResponse(BaseModel):
    id: UUID
    name: str
    chat_type: ChatType
    account_id: UUID
    created_at: datetime
    updated_at: datetime
    active: bool


class BranchInfo(BaseModel):
    branch_id: UUID


class QAPair(BaseModel):
    question: str
    response: str
    response_id: str = Field(..., description="Unique ID for the response")
    timestamp: datetime
    branches: List[str] = Field(default_factory=list, description="List of branch chat IDs")


class ChatContent(BaseModel):
    chat: ChatResponse
    qa_pairs: List[QAPair]
    active_branch_id: Optional[UUID] = None