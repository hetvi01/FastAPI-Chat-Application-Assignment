from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.message import BranchCreate, BranchResponse, BranchTreeResponse
from app.services.chat_service import ChatService

router = APIRouter()


@router.post("/create-branch", response_model=BranchResponse)
async def create_branch(
    branch: BranchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a branch from a specific message.
    """
    chat_service = ChatService(db)
    
    # Check if the chat exists and user has access
    chat = await chat_service.get_chat(branch.chat_id)
    if chat.account_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to create branches from this chat")
    
    result = await chat_service.create_branch(
        chat_id=branch.chat_id,
        response_id=branch.response_id,
        account_id=current_user.id,
        name=branch.name
    )
    
    return BranchResponse(
        id=result["branch_id"],
        name=result["name"],
        parent_chat_id=result["parent_chat_id"],
        parent_response_id=result["parent_response_id"],
        created_at=result.get("created_at")  
    )


@router.get("/get-branches", response_model=List[BranchResponse])
async def get_branches(
    chat_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all branches for a chat.
    """
    chat_service = ChatService(db)
    
    # Check if the chat exists and user has access
    chat = await chat_service.get_chat(chat_id)
    if chat.account_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view branches for this chat")
    
    branches = await chat_service.get_branches(chat_id)
    
    return [
        BranchResponse(
            id=branch.id,
            name=branch.name,
            parent_chat_id=chat_id,
            parent_response_id="",  
            created_at=branch.created_at
        )
        for branch in branches
    ]


@router.get("/get-branch-tree", response_model=BranchTreeResponse)
async def get_branch_tree(
    chat_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a complete tree of all branches for a conversation.
    """
    chat_service = ChatService(db)
    
    # Check if the chat exists and user has access
    chat = await chat_service.get_chat(chat_id)
    if chat.account_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view branch tree for this chat")
    
    tree = await chat_service.build_branch_tree(chat_id)
    
    return BranchTreeResponse(
        root_id=chat_id,
        tree=tree
    )


@router.put("/set-active-branch", status_code=status.HTTP_200_OK)
async def set_active_branch(
    chat_id: UUID,
    branch_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Set a specific branch as active.
    """
    chat_service = ChatService(db)
    
    # Check if the chat exists and user has access
    chat = await chat_service.get_chat(chat_id)
    if chat.account_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this chat")
    
    # Set the branch as active in the database
    result = await chat_service.set_active_branch(chat_id, branch_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="No branch found")
    
    return {"message": "Branch activated successfully"}