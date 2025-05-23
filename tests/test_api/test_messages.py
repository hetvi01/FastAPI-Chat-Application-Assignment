import pytest
from unittest.mock import AsyncMock, patch
from fastapi import status
from uuid import UUID
import datetime

from app.models.user import User


@pytest.mark.asyncio
async def test_add_message_success(client, override_get_db, mock_db_session):
    # Arrange
    mock_user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
    mock_chat_id = UUID("223e4567-e89b-12d3-a456-426614174000")
    mock_message_id = UUID("323e4567-e89b-12d3-a456-426614174000")
    mock_question = "What is the capital of France?"
    mock_response = "The capital of France is Paris."
    
    # Mock current_user dependency
    with patch("app.api.deps.get_current_user") as mock_get_current_user:
        mock_get_current_user.return_value = AsyncMock(
            id=mock_user_id,
            is_active=True,
            spec=User
        )
        
        # Mock chat service get_chat method
        mock_db_session.execute.return_value.scalar_one.return_value = AsyncMock(
            id=mock_chat_id,
            account_id=mock_user_id
        )
        
        # Mock AI response generator
        with patch("app.utils.mock_ai.generate_ai_response") as mock_ai_response:
            mock_ai_response.return_value = {
                "response": mock_response,
                "confidence": 0.95,
                "source": "knowledge base",
                "processing_time_ms": 150
            }
            
            # Mock chat service add_message method
            mock_timestamp = datetime.datetime.now()
            mock_db_session.execute.return_value.mappings.return_value.one.return_value = {
                "response_id": mock_message_id,
                "question": mock_question,
                "response": mock_response,
                "timestamp": mock_timestamp
            }
            
            # Act
            response = client.post(
                "/api/v1/messages/add-message",
                json={
                    "chat_id": str(mock_chat_id),
                    "question": mock_question
                }
            )
            
            # Assert
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["response_id"] == str(mock_message_id)
            assert data["question"] == mock_question
            assert data["response"] == mock_response
            assert "timestamp" in data


@pytest.mark.asyncio
async def test_add_message_unauthorized(client, override_get_db, mock_db_session):
    # Arrange
    mock_user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
    mock_other_user_id = UUID("423e4567-e89b-12d3-a456-426614174000")
    mock_chat_id = UUID("223e4567-e89b-12d3-a456-426614174000")
    mock_question = "What is the capital of France?"
    
    # Mock current_user dependency
    with patch("app.api.deps.get_current_user") as mock_get_current_user:
        mock_get_current_user.return_value = AsyncMock(
            id=mock_user_id,
            is_active=True,
            spec=User
        )
        
        # Mock chat service get_chat method with different owner
        mock_db_session.execute.return_value.scalar_one.return_value = AsyncMock(
            id=mock_chat_id,
            account_id=mock_other_user_id  # Different user owns the chat
        )
        
        # Act
        response = client.post(
            "/api/v1/messages/add-message",
            json={
                "chat_id": str(mock_chat_id),
                "question": mock_question
            }
        )
        
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert data["detail"] == "Not authorized to add messages to this chat"


@pytest.mark.asyncio
async def test_add_message_ai_integration(client, override_get_db, mock_db_session):
    # Arrange
    mock_user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
    mock_chat_id = UUID("223e4567-e89b-12d3-a456-426614174000")
    mock_message_id = UUID("323e4567-e89b-12d3-a456-426614174000")
    mock_question = "Tell me something interesting"
    mock_response = "The Great Wall of China is not visible from space with the naked eye, contrary to popular belief."
    
    # Mock current_user dependency
    with patch("app.api.deps.get_current_user") as mock_get_current_user:
        mock_get_current_user.return_value = AsyncMock(
            id=mock_user_id,
            is_active=True,
            spec=User
        )
        
        # Mock chat service get_chat method
        mock_db_session.execute.return_value.scalar_one.return_value = AsyncMock(
            id=mock_chat_id,
            account_id=mock_user_id
        )
        
        # Mock AI response generator
        with patch("app.utils.mock_ai.generate_ai_response") as mock_ai_response:
            mock_ai_response.return_value = {
                "response": mock_response,
                "confidence": 0.87,
                "source": "facts database",
                "processing_time_ms": 200
            }
            
            # Mock chat service add_message method to verify AI metadata is passed through
            mock_db_session.execute.return_value.mappings.return_value.one.return_value = {
                "response_id": mock_message_id,
                "question": mock_question,
                "response": mock_response,
                "timestamp": datetime.datetime.now()
            }
            
            # Act
            response = client.post(
                "/api/v1/messages/add-message",
                json={
                    "chat_id": str(mock_chat_id),
                    "question": mock_question
                }
            )
            
            # Assert
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["question"] == mock_question
            assert data["response"] == mock_response
            
            # Verify AI response was correctly used
            mock_ai_response.assert_called_once_with(mock_question)
            
            # We could also check that chat_service.add_message was called with the right parameters
            # if we had a way to inspect the mock_db_session's calls 