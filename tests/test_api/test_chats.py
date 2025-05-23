import pytest
from unittest.mock import AsyncMock, patch
from fastapi import status
from uuid import UUID

from app.models.user import User


@pytest.mark.asyncio
async def test_create_chat_success(client, override_get_db, mock_db_session):
    # Arrange
    mock_user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
    mock_chat_id = UUID("223e4567-e89b-12d3-a456-426614174000")
    mock_chat_name = "Test Chat"
    
    # Mock current_user dependency
    with patch("app.api.deps.get_current_user") as mock_get_current_user:
        mock_get_current_user.return_value = AsyncMock(
            id=mock_user_id,
            is_active=True,
            spec=User
        )
        
        # Mock chat service create_chat method
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = AsyncMock(
            id=mock_chat_id,
            name=mock_chat_name,
            account_id=mock_user_id,
            chat_type="general"
        )
        
        # Act
        response = client.post(
            "/api/v1/chats/create-chat",
            json={
                "name": mock_chat_name,
                "chat_type": "general"
            }
        )
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["id"] == str(mock_chat_id)
        assert data["name"] == mock_chat_name
        assert data["account_id"] == str(mock_user_id)
        assert data["chat_type"] == "general"


@pytest.mark.asyncio
async def test_get_chat_success(client, override_get_db, mock_db_session):
    # Arrange
    mock_user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
    mock_chat_id = UUID("223e4567-e89b-12d3-a456-426614174000")
    mock_chat_name = "Test Chat"
    
    # Mock current_user dependency
    with patch("app.api.deps.get_current_user") as mock_get_current_user:
        mock_get_current_user.return_value = AsyncMock(
            id=mock_user_id,
            is_active=True,
            spec=User
        )
        
        # Mock chat service get_chat_with_content method
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = {
            "chat": AsyncMock(
                id=mock_chat_id,
                name=mock_chat_name,
                account_id=mock_user_id,
                chat_type="general"
            ),
            "messages": [
                AsyncMock(
                    id=UUID("323e4567-e89b-12d3-a456-426614174000"),
                    content="Hello",
                    chat_id=mock_chat_id,
                    branch_id=None
                )
            ]
        }
        
        # Act
        response = client.get(
            f"/api/v1/chats/get-chat?chat_id={mock_chat_id}"
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "chat" in data
        assert "messages" in data
        assert data["chat"]["id"] == str(mock_chat_id)
        assert data["chat"]["account_id"] == str(mock_user_id)
        assert len(data["messages"]) == 1


@pytest.mark.asyncio
async def test_get_chat_unauthorized(client, override_get_db, mock_db_session):
    # Arrange
    mock_user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
    mock_other_user_id = UUID("423e4567-e89b-12d3-a456-426614174000")
    mock_chat_id = UUID("223e4567-e89b-12d3-a456-426614174000")
    
    # Mock current_user dependency
    with patch("app.api.deps.get_current_user") as mock_get_current_user:
        mock_get_current_user.return_value = AsyncMock(
            id=mock_user_id,
            is_active=True,
            spec=User
        )
        
        # Mock chat service get_chat_with_content method with different owner
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = {
            "chat": AsyncMock(
                id=mock_chat_id,
                name="Test Chat",
                account_id=mock_other_user_id,  # Different user
                chat_type="general"
            ),
            "messages": []
        }
        
        # Act
        response = client.get(
            f"/api/v1/chats/get-chat?chat_id={mock_chat_id}"
        )
        
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert data["detail"] == "Not authorized to access this chat"


@pytest.mark.asyncio
async def test_update_chat_success(client, override_get_db, mock_db_session):
    # Arrange
    mock_user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
    mock_chat_id = UUID("223e4567-e89b-12d3-a456-426614174000")
    
    # Mock current_user dependency
    with patch("app.api.deps.get_current_user") as mock_get_current_user:
        mock_get_current_user.return_value = AsyncMock(
            id=mock_user_id,
            is_active=True,
            spec=User
        )
        
        # Mock chat service get_chat method
        mock_db_session.execute.return_value.scalar_one.side_effect = [
            # First call for get_chat
            AsyncMock(
                id=mock_chat_id,
                name="Old Name",
                account_id=mock_user_id,
                chat_type="general"
            ),
            # Second call for update_chat
            AsyncMock(
                id=mock_chat_id,
                name="New Name",
                account_id=mock_user_id,
                chat_type="general"
            )
        ]
        
        # Act
        response = client.put(
            f"/api/v1/chats/update-chat?chat_id={mock_chat_id}",
            json={"name": "New Name"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(mock_chat_id)
        assert data["name"] == "New Name"
        assert data["account_id"] == str(mock_user_id)


@pytest.mark.asyncio
async def test_delete_chat_success(client, override_get_db, mock_db_session):
    # Arrange
    mock_user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
    mock_chat_id = UUID("223e4567-e89b-12d3-a456-426614174000")
    
    # Mock current_user dependency
    with patch("app.api.deps.get_current_user") as mock_get_current_user:
        mock_get_current_user.return_value = AsyncMock(
            id=mock_user_id,
            is_active=True,
            spec=User
        )
        
        # Mock chat service delete_chat method
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = True
        
        # Act
        response = client.delete(
            f"/api/v1/chats/delete-chat?chat_id={mock_chat_id}"
        )
        
        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.content == b""  # No content for 204 responses


@pytest.mark.asyncio
async def test_delete_chat_failure(client, override_get_db, mock_db_session):
    # Arrange
    mock_user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
    mock_chat_id = UUID("223e4567-e89b-12d3-a456-426614174000")
    
    # Mock current_user dependency
    with patch("app.api.deps.get_current_user") as mock_get_current_user:
        mock_get_current_user.return_value = AsyncMock(
            id=mock_user_id,
            is_active=True,
            spec=User
        )
        
        # Mock chat service delete_chat method - failure case
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = False
        
        # Act
        response = client.delete(
            f"/api/v1/chats/delete-chat?chat_id={mock_chat_id}"
        )
        
        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert data["detail"] == "Failed to delete chat" 