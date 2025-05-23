import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone

from app.models.chat import Chat, ChatType, Conversation
from app.services.chat_service import ChatService


@pytest.fixture
def mock_chat_repo():
    return AsyncMock()


@pytest.fixture
def mock_branch_repo():
    return AsyncMock()


@pytest.fixture
def mock_message_repo():
    return AsyncMock()


@pytest.fixture
def mock_chat_content_repo():
    with patch('app.repositories.chat_repository.ChatContentRepository') as mock:
        # Setup common mock returns
        mock.get_chat_content.return_value = {"messages": [], "branches": []}
        yield mock


@pytest.fixture
def chat_service(mock_chat_repo, mock_branch_repo, mock_message_repo, mock_chat_content_repo):
    service = ChatService(None)  # We'll mock the db_session
    service.chat_repo = mock_chat_repo
    service.branch_repo = mock_branch_repo
    service.message_repo = mock_message_repo
    return service


@pytest.mark.asyncio
async def test_create_chat(chat_service, mock_chat_repo):
    # Setup
    account_id = uuid4()
    chat_name = "Test Chat"
    chat_type = ChatType.PERSONAL
    
    mock_chat = Chat(
        id=uuid4(),
        account_id=account_id,
        name=chat_name,
        chat_type=chat_type
    )
    mock_chat_repo.create_chat.return_value = mock_chat
    
    # Execute
    with patch('app.services.chat_service.ChatContentRepository', autospec=True) as mock_content_repo:
        # Just make create_chat_content a no-op function that returns None
        mock_content_repo.create_chat_content = AsyncMock(return_value=None)
        result = await chat_service.create_chat(account_id, chat_name, chat_type)
    
    # Assert
    mock_chat_repo.create_chat.assert_called_once()
    assert result == mock_chat


@pytest.mark.asyncio
async def test_get_chat_not_found(chat_service, mock_chat_repo):
    # Setup
    mock_chat_repo.get_chat.return_value = None
    
    # Execute & Assert
    with pytest.raises(Exception):  # Should raise HTTPException but we don't have FastAPI context in unit tests
        await chat_service.get_chat(uuid4())


@pytest.mark.asyncio
async def test_get_chat(chat_service, mock_chat_repo):
    # Setup
    chat_id = uuid4()
    account_id = uuid4()
    
    mock_chat = Chat(
        id=chat_id,
        account_id=account_id,
        name="Test Chat",
        chat_type=ChatType.PERSONAL
    )
    mock_chat_repo.get_chat.return_value = mock_chat
    
    # Execute
    result = await chat_service.get_chat(chat_id)
    
    # Assert
    mock_chat_repo.get_chat.assert_called_once_with(chat_id)
    assert result == mock_chat
    assert result.id == chat_id
    assert result.account_id == account_id


@pytest.mark.asyncio
async def test_get_chat_with_content(chat_service, mock_chat_repo):
    # Setup
    chat_id = uuid4()
    account_id = uuid4()
    
    mock_chat = Chat(
        id=chat_id,
        account_id=account_id,
        name="Test Chat",
        chat_type=ChatType.PERSONAL
    )
    mock_chat_repo.get_chat.return_value = mock_chat
    
    # Match the structure expected by the service
    mock_content = {
        "chat_id": str(chat_id),
        "qa_pairs": [
            {"question": "Hello", "response": "World", "response_id": str(uuid4())}
        ],
        "active_branch_id": None,
        "branches": []
    }
    
    # Execute
    with patch('app.services.chat_service.ChatContentRepository', autospec=True) as mock_content_repo:
        mock_content_repo.get_chat_content = AsyncMock(return_value=mock_content)
        result = await chat_service.get_chat_with_content(chat_id)
    
    # Assert
    mock_chat_repo.get_chat.assert_called_once_with(chat_id)
    assert result["chat"] == mock_chat
    assert "qa_pairs" in result


@pytest.mark.asyncio
async def test_update_chat(chat_service, mock_chat_repo):
    # Setup
    chat_id = uuid4()
    account_id = uuid4()
    
    mock_chat = Chat(
        id=chat_id,
        account_id=account_id,
        name="Old Name",
        chat_type=ChatType.PERSONAL
    )
    
    updated_mock_chat = Chat(
        id=chat_id,
        account_id=account_id,
        name="New Name",
        chat_type=mock_chat.chat_type
    )
    
    mock_chat_repo.get_chat.return_value = mock_chat
    mock_chat_repo.update_chat.return_value = updated_mock_chat
    
    update_data = {"name": "New Name"}
    
    # Execute
    result = await chat_service.update_chat(chat_id, update_data)
    
    # Assert
    mock_chat_repo.update_chat.assert_called_once_with(chat_id, update_data)
    assert result.name == "New Name"
    assert result.id == chat_id


@pytest.mark.asyncio
async def test_add_message(chat_service):
    # Setup
    chat_id = uuid4()
    question = "What is the capital of France?"
    response = "The capital of France is Paris."
    metadata = {"confidence": 0.95}

    # Generate a response_id to use consistently
    mock_timestamp = datetime.now(timezone.utc)

    # Mock the chat object
    mock_chat = AsyncMock(id=chat_id, account_id=uuid4())

    # Execute
    with patch('app.services.chat_service.ChatContentRepository') as mock_content_repo_class:
        # Mock the add_message method
        mock_result = {
            "timestamp": mock_timestamp
        }
        mock_content_repo_class.add_message = AsyncMock(return_value=mock_result)
        
        # Mock uuid.uuid4 to return a predictable value for response_id
        mock_response_id = "mock-response-id-12345"
        with patch('uuid.uuid4', MagicMock(return_value=mock_response_id)):
            # Mock the get_chat method
            with patch.object(chat_service, 'get_chat', AsyncMock(return_value=mock_chat)):
                # Also patch the update_chat method
                with patch.object(chat_service.chat_repo, 'update_chat', AsyncMock()) as mock_update:
                    result = await chat_service.add_message(
                        chat_id=chat_id,
                        question=question,
                        response=response,
                        metadata=metadata
                    )

    # Assert
    # Note: positional parameters must match: question, response, response_id, chat_id, metadata
    mock_content_repo_class.add_message.assert_called_once()
    mock_update.assert_called_once()
    assert result["chat_id"] == chat_id
    assert result["question"] == question
    assert result["response"] == response
    assert result["metadata"] == metadata
    assert "response_id" in result
    assert "timestamp" in result


@pytest.mark.asyncio
async def test_create_branch(chat_service):
    # Setup
    chat_id = uuid4()
    response_id = str(uuid4())  # String, not UUID
    account_id = uuid4()
    branch_name = "New Branch"
    
    mock_branch_id = uuid4()
    
    # Mock the parent chat
    mock_parent_chat = AsyncMock(id=chat_id, name="Parent Chat")
    
    # Create mock data
    qa_pair = {
        "question": "Test question",
        "response": "Test response",
        "response_id": response_id,
        "metadata": {"confidence": 0.95}
    }
    
    # Mock branch chat
    mock_branch_chat = Chat(
        id=mock_branch_id,
        account_id=account_id,
        name=branch_name,
        chat_type=ChatType.BRANCH
    )
    
    # Mock conversation
    mock_conversation = Conversation(
        id=uuid4(),
        chat_id=mock_branch_id,
        account_id=account_id,
        name=branch_name
    )
    
    # Mock the return values
    with patch.object(chat_service, 'get_chat', AsyncMock(return_value=mock_parent_chat)):
        with patch('app.services.chat_service.ChatContentRepository') as mock_repo_class:
            mock_repo_class.get_qa_pair_by_response_id = AsyncMock(return_value=qa_pair)
            mock_repo_class.add_branch_to_message = AsyncMock()
            mock_repo_class.add_message = AsyncMock()
            mock_repo_class.create_chat_content = AsyncMock()
            
            with patch.object(chat_service, 'create_chat', AsyncMock(return_value=mock_branch_chat)):
                with patch.object(chat_service.chat_repo, 'create_conversation', AsyncMock(return_value=mock_conversation)):
                    result = await chat_service.create_branch(
                        chat_id=chat_id,
                        response_id=response_id,
                        account_id=account_id,
                        name=branch_name
                    )
    
    # Assert
    assert result["branch_id"] == mock_branch_id
    assert result["parent_chat_id"] == chat_id
    assert result["parent_response_id"] == response_id
    assert result["name"] == branch_name
    assert "created_at" in result


@pytest.mark.asyncio
async def test_get_branches(chat_service):
    # Setup
    chat_id = uuid4()
    branch_id1 = uuid4()
    branch_id2 = uuid4()
    
    # Mock branches as Chat objects that would be returned by chat_repo.get_chat
    mock_branch1 = Chat(id=branch_id1, name="Branch 1", account_id=uuid4(), chat_type=ChatType.BRANCH)
    mock_branch2 = Chat(id=branch_id2, name="Branch 2", account_id=uuid4(), chat_type=ChatType.BRANCH)
    
    # Mock chat content structure that contains branch references
    mock_chat_content = {
        "chat_id": str(chat_id),
        "qa_pairs": [
            {
                "question": "Q1",
                "response": "R1",
                "response_id": str(uuid4()),
                "branches": [str(branch_id1)]
            },
            {
                "question": "Q2",
                "response": "R2",
                "response_id": str(uuid4()),
                "branches": [str(branch_id2)]
            }
        ]
    }
    
    # Execute
    with patch.object(chat_service, 'get_chat', AsyncMock()):
        with patch('app.services.chat_service.ChatContentRepository') as mock_content_repo:
            mock_content_repo.get_chat_content = AsyncMock(return_value=mock_chat_content)
            
            # For each branch_id in the content, the service will call get_chat
            with patch.object(chat_service.chat_repo, 'get_chat', AsyncMock()) as mock_get_chat:
                # Setup sequential returns for multiple calls
                mock_get_chat.side_effect = [mock_branch1, mock_branch2]
                
                result = await chat_service.get_branches(chat_id)
    
    # Assert
    assert len(result) == 2
    assert result[0].id == branch_id1
    assert result[1].id == branch_id2
    assert mock_get_chat.call_count == 2


@pytest.mark.asyncio
async def test_delete_chat(chat_service, mock_chat_repo):
    # Setup
    chat_id = uuid4()
    account_id = uuid4()
    
    # Create a mock chat with the same account_id for authorization to pass
    mock_chat = Chat(
        id=chat_id,
        account_id=account_id,
        name="Test Chat", 
        chat_type=ChatType.PERSONAL
    )
    mock_chat_repo.get_chat.return_value = mock_chat
    
    # Execute
    with patch('app.services.chat_service.ChatContentRepository', autospec=True) as mock_content_repo:
        mock_content_repo.delete_chat_content = AsyncMock(return_value=True)
        # Mock the repository to return True
        mock_chat_repo.delete_chat = AsyncMock(return_value=True)
        result = await chat_service.delete_chat(chat_id, account_id)
    
    # Assert
    mock_chat_repo.delete_chat.assert_called_once()
    assert result is True 