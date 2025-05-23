from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.chat import ChatContent, ChatCreate, ChatUpdate, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter()


@router.post("/create-chat", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    chat: ChatCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new chat.
    """
    chat_service = ChatService(db)
    new_chat = await chat_service.create_chat(
        account_id=current_user.id,
        name=chat.name,
        chat_type=chat.chat_type
    )
    return new_chat


@router.get("/get-chat", response_model=ChatContent, status_code=status.HTTP_200_OK)
async def get_chat(
    chat_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get chat details and messages.
    """
    chat_service = ChatService(db)
    chat_data = await chat_service.get_chat_with_content(chat_id)
    
    # Check if user has access to this chat
    if chat_data["chat"].account_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this chat")
    return chat_data


@router.put("/update-chat", response_model=ChatResponse)
async def update_chat(
    chat_id: UUID,
    chat_update: ChatUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update chat metadata.
    """
    chat_service = ChatService(db)
    chat = await chat_service.get_chat(chat_id)
    
    # Check if user has access to this chat
    if chat.account_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this chat")
    
    update_data = chat_update.model_dump(exclude_unset=True)
    updated_chat = await chat_service.update_chat(chat_id, update_data)
    
    return updated_chat


@router.delete("/delete-chat", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    chat_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a chat.
    """
    chat_service = ChatService(db)
    result = await chat_service.delete_chat(chat_id, current_user.id)
    
    if not result:
        raise HTTPException(status_code=500, detail="Failed to delete chat") 