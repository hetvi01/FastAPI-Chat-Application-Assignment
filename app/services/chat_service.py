import uuid
from typing import Dict, List, Optional, Any
from uuid import UUID
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import Chat, ChatType, Conversation
from app.repositories.chat_repository import ChatRepository, ChatContentRepository
from app.schemas.chat import ChatResponse
from app.schemas.message import BranchTreeNode


class ChatService:
    def __init__(self, db_session: AsyncSession):
        self.chat_repo = ChatRepository(db_session)

    async def create_chat(self, account_id: UUID, name: str, chat_type: ChatType = ChatType.PERSONAL) -> Chat:
        chat = await self.chat_repo.create_chat(
            account_id=account_id,
            name=name,
            chat_type=chat_type
        )
        
        # Create chat content in MongoDB
        await ChatContentRepository.create_chat_content(chat.id)
        
        return chat

    async def get_chat(self, chat_id: UUID) -> Optional[Chat]:
        chat = await self.chat_repo.get_chat(chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        return chat

    async def get_chat_with_content(self, chat_id: UUID):
        # Get chat metadata from PostgreSQL
        chat = await self.get_chat(chat_id)
        
        # Get chat content from MongoDB
        content = await ChatContentRepository.get_chat_content(chat_id)
        if not content:
            raise HTTPException(status_code=404, detail="Chat content not found")
       
        return {
            "chat": chat,
            "qa_pairs": content['qa_pairs'],
            "active_branch_id": content['active_branch_id']
        }

    async def update_chat(self, chat_id: UUID, update_data: Dict[str, Any]) -> Chat:
        chat = await self.get_chat(chat_id)
        
        updated_chat = await self.chat_repo.update_chat(chat_id, update_data)
        if not updated_chat:
            raise HTTPException(status_code=500, detail="Failed to update chat")
        
        return updated_chat

    async def delete_chat(self, chat_id: UUID, account_id: UUID) -> bool:
        chat = await self.get_chat(chat_id)  # This will raise 404 if not found
        
        # Check if user owns the chat
        if chat.account_id != account_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this chat")
        
        # Delete chat content from MongoDB
        await ChatContentRepository.delete_chat_content(chat_id)
        
        # Delete chat from PostgreSQL
        result = await self.chat_repo.delete_chat(chat_id)
        
        return result

    async def get_user_chats(self, account_id: UUID) -> List[Chat]:
        return await self.chat_repo.get_user_chats(account_id)

    async def add_message(self, chat_id: UUID, question: str, response: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        chat = await self.get_chat(chat_id)  # This will raise 404 if not found
        
        # Generate a unique response ID
        response_id = str(uuid.uuid4())
        
        # Add message to MongoDB
        message = await ChatContentRepository.add_message(
            chat_id=chat_id,
            question=question,
            response=response,
            response_id=response_id,
            metadata=metadata
        )
        # Update chat's updated_at timestamp
        await self.chat_repo.update_chat(chat_id, {"updated_at": None})  # The repository will set the current timestamp
        
        return {
            "chat_id": chat_id,
            "response_id": response_id,
            "question": question,
            "response": response,
            "timestamp": message["timestamp"],
            "metadata": metadata
        }

    async def create_branch(self, chat_id: UUID, response_id: str, account_id: UUID, name: Optional[str] = None) -> Dict[str, Any]:
        # Check if parent chat exists
        parent_chat = await self.get_chat(chat_id)
        
        # Check if the response exists in the chat
        qa_pair = await ChatContentRepository.get_qa_pair_by_response_id(chat_id, response_id)
        if not qa_pair:
            raise HTTPException(status_code=404, detail="Oops! Given Response not found")
        
        # Create a new chat as a branch
        branch_name = name or f"Branch of {parent_chat.name}"
        branch_chat = await self.create_chat(
            account_id=account_id,
            name=branch_name,
            chat_type=ChatType.BRANCH
        )
        
        # Create conversation record linking the branch to the parent
        conversation = await self.chat_repo.create_conversation(
            chat_id=branch_chat.id,
            account_id=account_id,
            name=branch_name,
            parent_id=None  # This is the root conversation in the branch
        )
        
        # Add branch reference to the parent message
        await ChatContentRepository.add_branch_to_message(chat_id, response_id, branch_chat.id)
        
        # Copy the parent message content to the branch
        await ChatContentRepository.add_message(
            chat_id=branch_chat.id,
            question=qa_pair["question"],
            response=qa_pair["response"],
            response_id=str(uuid.uuid4()),  # Generate a new response ID for the branch
            metadata=qa_pair.get("metadata")  # Copy metadata if present
        )
        
        return {
            "branch_id": branch_chat.id,
            "parent_chat_id": chat_id,
            "parent_response_id": response_id,
            "name": branch_name,
            "created_at": datetime.now(timezone.utc)
        }   

    async def get_branches(self, chat_id: UUID) -> List[Chat]:
        # Get the chat to verify it exists
        await self.get_chat(chat_id)
        
        # Get chat content
        content = await ChatContentRepository.get_chat_content(chat_id)
        if not content:
            return []
            
        # Extract branch IDs from all messages
        branch_ids = set()
        for qa_pair in content.get("qa_pairs", []):
            branch_ids.update(qa_pair.get("branches", []))
            
        # Get branch chats
        branches = []
        for branch_id in branch_ids:
            try:
                branch = await self.chat_repo.get_chat(UUID(branch_id))
                if branch:
                    branches.append(branch)
            except ValueError:
                # Invalid UUID, skip
                pass
                
        return branches

    async def build_branch_tree(self, chat_id: UUID) -> BranchTreeNode:
        # Get the chat to verify it exists
        chat = await self.get_chat(chat_id)
        
        # Get all branches for this chat
        branches = await self.get_branches(chat_id)
        
        # Build a map of branch IDs to chats
        branch_map = {str(branch.id): branch for branch in branches}
        
        # Get chat content to find parent-child relationships
        content = await ChatContentRepository.get_chat_content(chat_id)
        
        # Map of response_id to branches
        response_branches = {}
        if content:
            for qa_pair in content.get("qa_pairs", []):
                response_id = qa_pair.get("response_id")
                if response_id:
                    response_branches[response_id] = qa_pair.get("branches", [])
        
        # Create the root node
        root_node = BranchTreeNode(
            id=chat.id,
            name=chat.name,
            parent_id=None,
            children=[]
        )
        
        # Helper function to recursively build the tree
        async def build_tree(node, branches_list):
            for branch_id in branches_list:
                if branch_id in branch_map:
                    branch = branch_map[branch_id]
                    child_node = BranchTreeNode(
                        id=branch.id,
                        name=branch.name,
                        parent_id=node.id,
                        children=[]
                    )
                    # Get child branches
                    branch_content = await ChatContentRepository.get_chat_content(branch.id)
                    if branch_content:
                        for qa in branch_content.get("qa_pairs", []):
                            await build_tree(child_node, qa.get("branches", []))
                    
                    node.children.append(child_node)
        
        # Build the tree starting from the root
        for qa_pair in content.get("qa_pairs", []):
            await build_tree(root_node, qa_pair.get("branches", []))
            
        return root_node 
    
    async def set_active_branch(self, chat_id: UUID, branch_id: UUID) -> bool:
        # First verify the chat exists
        chat = await self.get_chat(chat_id)
        
        # Check if this branch belongs to the chat
        branches = await self.get_branches(chat_id)
        branch_exists = any(str(branch.id) == str(branch_id) for branch in branches)
        
        if not branch_exists:
            raise HTTPException(status_code=404, detail="Branch not found for this chat")
        
        # Update the active branch in MongoDB
        result = await ChatContentRepository.set_active_branch(chat_id, branch_id)
        
        return result
