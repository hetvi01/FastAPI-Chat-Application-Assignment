import pytest
from unittest.mock import AsyncMock, patch
from fastapi import status
import datetime
from uuid import UUID

from app.models.user import User


@pytest.mark.asyncio
async def test_chat_flow_integration(client, override_get_db, mock_db_session):
    """
    Integration test for the complete chat flow:
    1. Register a user
    2. Login and get token
    3. Create a chat
    4. Send messages in the chat
    5. Create a branch
    6. Get branch tree
    """
    # Mock user and chat IDs
    mock_user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
    mock_chat_id = UUID("223e4567-e89b-12d3-a456-426614174000")
    mock_message_id = UUID("323e4567-e89b-12d3-a456-426614174000")
    mock_branch_id = UUID("423e4567-e89b-12d3-a456-426614174000")
    
    # Step 1: Register user
    user_email = "test@example.com"
    user_password = "password123"
    user_username = "testuser"
    
    # Mock user registration
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = AsyncMock(
        id=mock_user_id,
        email=user_email,
        username=user_username,
        password="hashed_password",
        is_active=True,
        is_superuser=False
    )
    
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": user_email,
            "username": user_username,
            "password": user_password
        }
    )
    assert register_response.status_code == status.HTTP_200_OK
    user_data = register_response.json()
    assert user_data["email"] == user_email
    
    # Step 2: Login
    # Mock authentication
    with patch("app.services.user_service.UserService.authenticate") as mock_authenticate:
        mock_authenticate.return_value = AsyncMock(
            id=mock_user_id,
            email=user_email,
            is_active=True
        )
        
        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": user_email, "password": user_password}
        )
        assert login_response.status_code == status.HTTP_200_OK
        token_data = login_response.json()
        assert "access_token" in token_data
        token = token_data["access_token"]
        
        # Use the token for subsequent requests
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 3: Create a chat
        # Mock current_user dependency for all subsequent requests
        with patch("app.api.deps.get_current_user") as mock_get_current_user:
            mock_get_current_user.return_value = AsyncMock(
                id=mock_user_id,
                email=user_email,
                username=user_username,
                is_active=True,
                spec=User
            )
            
            # Mock chat creation
            mock_db_session.execute.return_value.scalar_one_or_none.return_value = AsyncMock(
                id=mock_chat_id,
                name="Test Chat",
                account_id=mock_user_id,
                chat_type="general",
                created_at=datetime.datetime.now()
            )
            
            create_chat_response = client.post(
                "/api/v1/chats/create-chat",
                headers=headers,
                json={
                    "name": "Test Chat",
                    "chat_type": "general"
                }
            )
            assert create_chat_response.status_code == status.HTTP_201_CREATED
            chat_data = create_chat_response.json()
            assert chat_data["name"] == "Test Chat"
            assert chat_data["account_id"] == str(mock_user_id)
            
            # Step 4: Add message to chat
            # Mock get_chat for authorization check
            mock_db_session.execute.return_value.scalar_one.return_value = AsyncMock(
                id=mock_chat_id,
                account_id=mock_user_id
            )
            
            # Mock AI response
            with patch("app.utils.mock_ai.generate_ai_response") as mock_ai_response:
                mock_ai_response.return_value = {
                    "response": "This is an AI response",
                    "confidence": 0.95,
                    "source": "knowledge base",
                    "processing_time_ms": 150
                }
                
                # Mock add_message result
                mock_timestamp = datetime.datetime.now()
                mock_db_session.execute.return_value.mappings.return_value.one.return_value = {
                    "response_id": mock_message_id,
                    "question": "Test question",
                    "response": "This is an AI response",
                    "timestamp": mock_timestamp
                }
                
                add_message_response = client.post(
                    "/api/v1/messages/add-message",
                    headers=headers,
                    json={
                        "chat_id": str(mock_chat_id),
                        "question": "Test question"
                    }
                )
                assert add_message_response.status_code == status.HTTP_201_CREATED
                message_data = add_message_response.json()
                assert message_data["question"] == "Test question"
                assert message_data["response"] == "This is an AI response"
                
                # Step 5: Create a branch
                # Mock create_branch result
                mock_created_at = datetime.datetime.now()
                mock_db_session.execute.return_value.mappings.return_value.one.return_value = {
                    "branch_id": mock_branch_id,
                    "name": "Test Branch",
                    "parent_chat_id": mock_chat_id,
                    "parent_response_id": mock_message_id,
                    "created_at": mock_created_at
                }
                
                create_branch_response = client.post(
                    "/api/v1/branches/create-branch",
                    headers=headers,
                    json={
                        "chat_id": str(mock_chat_id),
                        "response_id": str(mock_message_id),
                        "name": "Test Branch"
                    }
                )
                assert create_branch_response.status_code == status.HTTP_200_OK
                branch_data = create_branch_response.json()
                assert branch_data["id"] == str(mock_branch_id)
                assert branch_data["name"] == "Test Branch"
                assert branch_data["parent_chat_id"] == str(mock_chat_id)
                
                # Step 6: Get branch tree
                # Mock build_branch_tree method
                mock_tree = {
                    "id": str(mock_chat_id),
                    "name": "Main Chat",
                    "children": [
                        {
                            "id": str(mock_branch_id),
                            "name": "Test Branch",
                            "children": []
                        }
                    ]
                }
                with patch("app.services.chat_service.ChatService.build_branch_tree") as mock_build_tree:
                    mock_build_tree.return_value = mock_tree
                    
                    get_tree_response = client.get(
                        f"/api/v1/branches/get-branch-tree?chat_id={mock_chat_id}",
                        headers=headers
                    )
                    assert get_tree_response.status_code == status.HTTP_200_OK
                    tree_data = get_tree_response.json()
                    assert tree_data["root_id"] == str(mock_chat_id)
                    assert "tree" in tree_data
                    assert tree_data["tree"] == mock_tree


@pytest.mark.asyncio
async def test_authentication_required(client):
    """
    Test that authentication is required for protected endpoints.
    """
    # Try to access protected endpoints without authentication
    endpoints = [
        {
            "url": "/api/v1/chats/create-chat",
            "method": "post",
            "json": {"name": "Test Chat", "chat_type": "general"}
        },
        {
            "url": "/api/v1/chats/get-chat?chat_id=123e4567-e89b-12d3-a456-426614174000",
            "method": "get"
        },
        {
            "url": "/api/v1/messages/add-message",
            "method": "post",
            "json": {"chat_id": "123e4567-e89b-12d3-a456-426614174000", "question": "Test"}
        },
        {
            "url": "/api/v1/branches/create-branch",
            "method": "post",
            "json": {
                "chat_id": "123e4567-e89b-12d3-a456-426614174000",
                "response_id": "223e4567-e89b-12d3-a456-426614174000",
                "name": "Test Branch"
            }
        }
    ]
    
    for endpoint in endpoints:
        if endpoint["method"] == "get":
            response = client.get(endpoint["url"])
        else:  # post
            response = client.post(endpoint["url"], json=endpoint.get("json", {}))
        
        # All should return 401 Unauthorized or 403 Forbidden
        assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)
        data = response.json()
        assert "detail" in data 