from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chat import Chat, Conversation
from app.db.mongodb import chat_content


class ChatRepository:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_chat(self, account_id: UUID, name: str, chat_type: str) -> Chat:
        chat = Chat(
            account_id=account_id,
            name=name,
            chat_type=chat_type
        )
        self.db_session.add(chat)
        await self.db_session.commit()
        await self.db_session.refresh(chat)
        return chat

    async def get_chat(self, chat_id: UUID) -> Optional[Chat]:
        query = select(Chat).where(Chat.id == chat_id)
        result = await self.db_session.execute(query)
        return result.scalars().first()

    async def get_chat_with_conversations(self, chat_id: UUID) -> Optional[Chat]:
        query = select(Chat).where(Chat.id == chat_id).options(
            selectinload(Chat.conversations)
        )
        result = await self.db_session.execute(query)
        return result.scalars().first()

    async def update_chat(self, chat_id: UUID, update_data: Dict[str, Any]) -> Optional[Chat]:
        # Update timestamp
        update_data["updated_at"] = datetime.now(timezone.utc)
        query = update(Chat).where(Chat.id == chat_id).values(**update_data).returning(Chat)
        result = await self.db_session.execute(query)
        await self.db_session.commit()
        return result.scalars().first()

    async def delete_chat(self, chat_id: UUID) -> bool:
        query = delete(Chat).where(Chat.id == chat_id)
        result = await self.db_session.execute(query)
        await self.db_session.commit()
        return result.rowcount > 0

    async def get_user_chats(self, account_id: UUID) -> List[Chat]:
        query = select(Chat).where(Chat.account_id == account_id)
        result = await self.db_session.execute(query)
        return result.scalars().all()

    async def create_conversation(self, chat_id: UUID, account_id: UUID, name: str, parent_id: Optional[UUID] = None) -> Conversation:
        conversation = Conversation(
            chat_id=chat_id,
            account_id=account_id,
            name=name,
            parent_id=parent_id
        )
        self.db_session.add(conversation)
        await self.db_session.commit()
        await self.db_session.refresh(conversation)
        return conversation

    async def get_conversation(self, conversation_id: UUID) -> Optional[Conversation]:
        query = select(Conversation).where(Conversation.id == conversation_id)
        result = await self.db_session.execute(query)
        return result.scalars().first()

    async def get_chat_conversations(self, chat_id: UUID) -> List[Conversation]:
        query = select(Conversation).where(Conversation.chat_id == chat_id)
        result = await self.db_session.execute(query)
        return result.scalars().all()

    async def get_conversation_tree(self, chat_id: UUID) -> List[Tuple[Conversation, Optional[Conversation]]]:
        # Get all conversations in a chat with their parent relationships
        query = select(Conversation).where(Conversation.chat_id == chat_id).options(
            selectinload(Conversation.parent)
        )
        result = await self.db_session.execute(query)
        conversations = result.scalars().all()
        return [(conv, conv.parent) for conv in conversations]


class ChatContentRepository:
    @staticmethod
    async def create_chat_content(chat_id: UUID):
        await chat_content.insert_one({
            "chat_id": str(chat_id),
            "qa_pairs": []
        })

    @staticmethod
    async def get_chat_content(chat_id: UUID):
        return await chat_content.find_one({"chat_id": str(chat_id)})


    async def add_message(
    chat_id: UUID,
    question: str,
    response: str,
    response_id: str,
    metadata: Optional[Dict[str, Any]] = None
):
        message_data = {
            "question": question,
            "response": response,
            "response_id": response_id,
            "timestamp": datetime.now(timezone.utc),
            "branches": []
        }

        if metadata:
            message_data["metadata"] = metadata

        result = await chat_content.update_one(
            {"chat_id": str(chat_id)},                     
            {"$push": {"qa_pairs": message_data}},         
            # upsert=True                                    
        )
        return result


    @staticmethod
    async def add_branch_to_message(chat_id: UUID, response_id: str, branch_chat_id: UUID):
        await chat_content.update_one(
            {"chat_id": str(chat_id), "qa_pairs.response_id": response_id},
            {"$push": {"qa_pairs.$.branches": str(branch_chat_id)}}
        )

    
    @staticmethod
    async def get_qa_pair_by_response_id(chat_id: UUID, response_id: str):
        # First find the document
        document = await chat_content.find_one({"chat_id": str(chat_id)})
        if not document or "qa_pairs" not in document:
            return None
            
        for qa_pair in document["qa_pairs"]:
            if qa_pair.get("response_id") == response_id:
                return qa_pair
                
        return None

    @staticmethod
    async def delete_chat_content(chat_id: UUID):
        await chat_content.delete_one({"chat_id": str(chat_id)}) 
    
    @staticmethod
    async def set_active_branch(chat_id: UUID, branch_id: UUID) -> bool:
        result = await chat_content.update_one(
            {"chat_id": str(chat_id)},
            {"$set": {"active_branch_id": str(branch_id)}}
        )
        return result.modified_count > 0