import pytest
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4
from datetime import datetime

from app.models.user import User
from app.services.user_service import UserService
from app.core.security import verify_password


@pytest.fixture
def mock_user_repo():
    return AsyncMock()


@pytest.fixture
def user_service(mock_user_repo):
    service = UserService(None)  # We'll mock the db_session
    service.user_repo = mock_user_repo
    return service


@pytest.mark.asyncio
async def test_get_by_email(user_service, mock_user_repo):
    # Setup
    email = "test@example.com"
    mock_user = User(
        id=uuid4(),
        email=email,
        username="testuser",
        hashed_password="hashed_password",
        is_active=True,
        created_at=datetime.now()
    )
    mock_user_repo.get_by_email.return_value = mock_user
    
    # Execute
    result = await user_service.get_by_email(email)
    
    # Assert
    mock_user_repo.get_by_email.assert_called_once_with(email)
    assert result == mock_user


@pytest.mark.asyncio
async def test_get_by_email_not_found(user_service, mock_user_repo):
    # Setup
    email = "nonexistent@example.com"
    mock_user_repo.get_by_email.return_value = None
    
    # Execute
    result = await user_service.get_by_email(email)
    
    # Assert
    mock_user_repo.get_by_email.assert_called_once_with(email)
    assert result is None


@pytest.mark.asyncio
async def test_create_user(user_service, mock_user_repo):
    # Setup
    email = "new@example.com"
    username = "newuser"
    password = "password123"
    
    mock_user = User(
        id=uuid4(),
        email=email,
        username=username,
        hashed_password="hashed_password",
        is_active=True,
        created_at=datetime.now()
    )
    mock_user_repo.create.return_value = mock_user
    
    # Execute
    with patch("app.services.user_service.get_password_hash") as mock_hash_pw:
        mock_hash_pw.return_value = "hashed_password"
        result = await user_service.create_user(email, username, password)
    
    # Assert
    mock_user_repo.create.assert_called_once()
    assert result == mock_user
    assert result.email == email
    assert result.username == username


@pytest.mark.asyncio
async def test_authenticate_success(user_service, mock_user_repo):
    # Setup
    email = "test@example.com"
    password = "password123"
    
    mock_user = User(
        id=uuid4(),
        email=email,
        username="testuser",
        hashed_password="hashed_password",
        is_active=True,
        created_at=datetime.now()
    )
    mock_user_repo.get_by_email.return_value = mock_user
    
    # Execute
    with patch("app.services.user_service.verify_password") as mock_verify:
        mock_verify.return_value = True
        result = await user_service.authenticate(email, password)
    
    # Assert
    mock_user_repo.get_by_email.assert_called_once_with(email)
    assert result == mock_user


@pytest.mark.asyncio
async def test_authenticate_invalid_password(user_service, mock_user_repo):
    # Setup
    email = "test@example.com"
    password = "wrong_password"
    
    mock_user = User(
        id=uuid4(),
        email=email,
        username="testuser",
        hashed_password="hashed_password",
        is_active=True,
        created_at=datetime.now()
    )
    mock_user_repo.get_by_email.return_value = mock_user
    
    # Execute
    with patch("app.services.user_service.verify_password") as mock_verify:
        mock_verify.return_value = False
        result = await user_service.authenticate(email, password)
    
    # Assert
    mock_user_repo.get_by_email.assert_called_once_with(email)
    assert result is None


@pytest.mark.asyncio
async def test_authenticate_user_not_found(user_service, mock_user_repo):
    # Setup
    email = "nonexistent@example.com"
    password = "password123"
    
    mock_user_repo.get_by_email.return_value = None
    
    # Execute
    result = await user_service.authenticate(email, password)
    
    # Assert
    mock_user_repo.get_by_email.assert_called_once_with(email)
    assert result is None 