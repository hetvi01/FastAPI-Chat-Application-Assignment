import pytest
from unittest.mock import AsyncMock, patch
from fastapi import status
from uuid import UUID
import datetime

from app.models.user import User


@pytest.mark.asyncio
async def test_create_branch_success(client, override_get_db, mock_db_session):
    # Arrange
    mock_user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
    mock_chat_id = UUID("223e4567-e89b-12d3-a456-426614174000")
    mock_response_id = UUID("323e4567-e89b-12d3-a456-426614174000")
    mock_branch_id = UUID("423e4567-e89b-12d3-a456-426614174000")
    mock_branch_name = "Alternative Path"
    
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
        
        # Mock chat service create_branch method
        mock_created_at = datetime.datetime.now()
        mock_db_session.execute.return_value.mappings.return_value.one.return_value = {
            "branch_id": mock_branch_id,
            "name": mock_branch_name,
            "parent_chat_id": mock_chat_id,
            "parent_response_id": mock_response_id,
            "created_at": mock_created_at
        }
        
        # Act
        response = client.post(
            "/api/v1/branches/create-branch",
            json={
                "chat_id": str(mock_chat_id),
                "response_id": str(mock_response_id),
                "name": mock_branch_name
            }
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(mock_branch_id)
        assert data["name"] == mock_branch_name
        assert data["parent_chat_id"] == str(mock_chat_id)
        assert data["parent_response_id"] == str(mock_response_id)
        assert "created_at" in data


@pytest.mark.asyncio
async def test_create_branch_unauthorized(client, override_get_db, mock_db_session):
    # Arrange
    mock_user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
    mock_other_user_id = UUID("523e4567-e89b-12d3-a456-426614174000")
    mock_chat_id = UUID("223e4567-e89b-12d3-a456-426614174000")
    mock_response_id = UUID("323e4567-e89b-12d3-a456-426614174000")
    mock_branch_name = "Alternative Path"
    
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
            "/api/v1/branches/create-branch",
            json={
                "chat_id": str(mock_chat_id),
                "response_id": str(mock_response_id),
                "name": mock_branch_name
            }
        )
        
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert data["detail"] == "Not authorized to create branches from this chat"


@pytest.mark.asyncio
async def test_get_branches_success(client, override_get_db, mock_db_session):
    # Arrange
    mock_user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
    mock_chat_id = UUID("223e4567-e89b-12d3-a456-426614174000")
    mock_branch_id_1 = UUID("423e4567-e89b-12d3-a456-426614174000")
    mock_branch_id_2 = UUID("523e4567-e89b-12d3-a456-426614174000")
    
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
                account_id=mock_user_id
            ),
            # Second call for get_branches
            [
                AsyncMock(
                    id=mock_branch_id_1,
                    name="Branch 1",
                    created_at=datetime.datetime.now()
                ),
                AsyncMock(
                    id=mock_branch_id_2,
                    name="Branch 2",
                    created_at=datetime.datetime.now()
                )
            ]
        ]
        
        # Act
        response = client.get(
            f"/api/v1/branches/get-branches?chat_id={mock_chat_id}"
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["id"] in [str(mock_branch_id_1), str(mock_branch_id_2)]
        assert data[1]["id"] in [str(mock_branch_id_1), str(mock_branch_id_2)]
        assert data[0]["id"] != data[1]["id"]


@pytest.mark.asyncio
async def test_get_branch_tree_success(client, override_get_db, mock_db_session):
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
        mock_db_session.execute.return_value.scalar_one.return_value = AsyncMock(
            id=mock_chat_id,
            account_id=mock_user_id
        )
        
        # Mock chat service build_branch_tree method
        mock_tree = {
            "id": str(mock_chat_id),
            "name": "Main Chat",
            "children": [
                {
                    "id": "423e4567-e89b-12d3-a456-426614174000",
                    "name": "Branch 1",
                    "children": []
                },
                {
                    "id": "523e4567-e89b-12d3-a456-426614174000",
                    "name": "Branch 2",
                    "children": [
                        {
                            "id": "623e4567-e89b-12d3-a456-426614174000",
                            "name": "Sub-branch",
                            "children": []
                        }
                    ]
                }
            ]
        }
        # Mocking the build_branch_tree method
        with patch("app.services.chat_service.ChatService.build_branch_tree") as mock_build_tree:
            mock_build_tree.return_value = mock_tree
            
            # Act
            response = client.get(
                f"/api/v1/branches/get-branch-tree?chat_id={mock_chat_id}"
            )
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["root_id"] == str(mock_chat_id)
            assert "tree" in data
            assert data["tree"] == mock_tree


@pytest.mark.asyncio
async def test_set_active_branch_success(client, override_get_db, mock_db_session):
    # Arrange
    mock_user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
    mock_chat_id = UUID("223e4567-e89b-12d3-a456-426614174000")
    mock_branch_id = UUID("423e4567-e89b-12d3-a456-426614174000")
    
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
        
        # Mock the set_active_branch method
        with patch("app.services.chat_service.ChatService.set_active_branch") as mock_set_active:
            mock_set_active.return_value = True
            
            # Act
            response = client.put(
                f"/api/v1/branches/set-active-branch?chat_id={mock_chat_id}&branch_id={mock_branch_id}"
            )
            
            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["message"] == "Branch activated successfully"


@pytest.mark.asyncio
async def test_set_active_branch_not_found(client, override_get_db, mock_db_session):
    # Arrange
    mock_user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
    mock_chat_id = UUID("223e4567-e89b-12d3-a456-426614174000")
    mock_branch_id = UUID("423e4567-e89b-12d3-a456-426614174000")
    
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
        
        # Mock the set_active_branch method to return False (not found)
        with patch("app.services.chat_service.ChatService.set_active_branch") as mock_set_active:
            mock_set_active.return_value = False
            
            # Act
            response = client.put(
                f"/api/v1/branches/set-active-branch?chat_id={mock_chat_id}&branch_id={mock_branch_id}"
            )
            
            # Assert
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert data["detail"] == "No branch found" 