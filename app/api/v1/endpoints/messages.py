from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.message import MessageCreate, MessageResponse
from app.services.chat_service import ChatService
from app.utils.mock_ai import generate_ai_response

router = APIRouter()


@router.post("/add-message", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def add_message(
    message: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add a message to a chat.
    """
    chat_service = ChatService(db)
    
    # Check if the chat exists and user has access
    chat = await chat_service.get_chat(message.chat_id)
    if chat.account_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to add messages to this chat")
    
    # Call the mock AI service 
    ai_result = await generate_ai_response(message.question)
    ai_response = ai_result["response"]
    
    # Extract metadata from AI response for storage
    ai_metadata = {
        "confidence": ai_result.get("confidence"),
        "source": ai_result.get("source"),
        "processing_time_ms": ai_result.get("processing_time_ms")
    }
    
    result = await chat_service.add_message(
        chat_id=message.chat_id,
        question=message.question,
        response=ai_response,
        metadata=ai_metadata
    )
    
    return MessageResponse(
        response_id=result["response_id"],
        question=result["question"],
        response=result["response"],
        timestamp=result.get("timestamp")  # This might come from the service or be None
    ) 