from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, UUID4, Field
from uuid import UUID


class MessageCreate(BaseModel):
    chat_id: UUID
    question: str


class MessageResponse(BaseModel):
    response_id: str
    question: str
    response: str
    timestamp: datetime
    branches: List[str] = []
    metadata: Optional[Dict[str, Any]] = None


class BranchCreate(BaseModel):
    chat_id: UUID
    response_id: str
    name: Optional[str] = None


class BranchResponse(BaseModel):
    id: UUID
    name: str
    parent_chat_id: UUID
    parent_response_id: str
    created_at: datetime


class BranchTreeNode(BaseModel):
    id: UUID
    name: str
    parent_id: Optional[UUID] = None
    children: List["BranchTreeNode"] = []


class BranchTreeResponse(BaseModel):
    root_id: UUID
    tree: BranchTreeNode


# Support for recursive Pydantic models
BranchTreeNode.update_forward_refs() 