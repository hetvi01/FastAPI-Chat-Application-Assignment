import pytest
from unittest.mock import AsyncMock, patch
from fastapi import status

from app.schemas.user import UserCreate, UserResponse


@pytest.mark.asyncio
async def test_register_success(client, override_get_db, mock_db_session):
    # Arrange
    mock_user_id = "123e4567-e89b-12d3-a456-426614174000"
    mock_email = "test@example.com"
    mock_username = "testuser"
    
    # Mock user_service.get_by_email and user_service.get_by_username to return None (user doesn't exist)
    mock_db_session.execute.return_value.scalars.return_value.first.return_value = None
    
    # Mock the user object that will be returned after creation
    created_user = AsyncMock(
        id=mock_user_id,
        email=mock_email,
        username=mock_username,
        is_active=True,
        is_superuser=False
    )
    
    # Return None for checks, then return the created user
    mock_db_session.execute.return_value.scalars.return_value.first.side_effect = [None, None, created_user]
    
    # Act
    with patch('app.services.user_service.get_password_hash', return_value="hashed_password"):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": mock_email,
                "username": mock_username,
                "password": "password123"
            }
        )
    
    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == mock_email
    assert data["username"] == mock_username
    assert data["is_active"] is True
    assert data["is_superuser"] is False

