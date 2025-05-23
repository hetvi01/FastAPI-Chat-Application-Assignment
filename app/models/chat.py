from enum import Enum
from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
import uuid

from app.models.base import BaseModel


class ChatType(str, Enum):
    PERSONAL = "personal"
    BRANCH = "branch"


class ChatBase(SQLModel):
    name: str
    chat_type: ChatType
    active: bool = True


class Chat(ChatBase, BaseModel, table=True):
    __tablename__ = "chats"
    
    account_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    
    # Relationships
    conversations: List["Conversation"] = Relationship(back_populates="chat")


class ConversationBase(SQLModel):
    name: str
    deleted: bool = False


class Conversation(ConversationBase, BaseModel, table=True):
    __tablename__ = "conversations"
    
    chat_id: uuid.UUID = Field(foreign_key="chats.id", index=True)
    account_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    parent_id: Optional[uuid.UUID] = Field(default=None, foreign_key="conversations.id", nullable=True)
    
    # Relationships
    chat: Chat = Relationship(back_populates="conversations")
    parent: Optional["Conversation"] = Relationship(
        sa_relationship_kwargs={"remote_side": "Conversation.id"}
    )
    children: List["Conversation"] = Relationship(
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class ChatCreate(ChatBase):
    pass


class ChatUpdate(SQLModel):
    name: Optional[str] = None
    active: Optional[bool] = None


class ConversationCreate(ConversationBase):
    chat_id: uuid.UUID
    parent_id: Optional[uuid.UUID] = None


class ConversationUpdate(SQLModel):
    name: Optional[str] = None
    deleted: Optional[bool] = None 